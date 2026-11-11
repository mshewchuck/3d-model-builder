import itertools

import numpy as np

import pytest

from modelbuilder.templates import CurvedReturnTemplate
from modelbuilder.threemf import write_3mf


@pytest.fixture(scope="module")
def tmpl():
    return CurvedReturnTemplate()


@pytest.fixture(scope="module")
def result(tmpl):
    return tmpl.build(tmpl.defaults())


def test_parts_are_single_solids(result):
    names = [p.name for p in result.print_parts]
    assert sum(n.startswith("Chute half") for n in names) == 2
    assert sum(n.startswith("Swivel ring") for n in names) == 1
    assert names.count("Hanger") == 1  # default: hangs from the rim block, no hooks
    for p in result.print_parts:
        # The print-in-place swivel is two interlocked, separate pieces by design.
        expected = 2 if p.name.startswith("Swivel") else 1
        assert len(p.solid.decompose()) == expected, p.name


def test_fixed_ring_option(tmpl):
    r = tmpl.build(tmpl.defaults() | {"swivel": 0})
    names = [p.name for p in r.print_parts]
    assert "Ring" in names
    assert all(len(p.solid.decompose()) == 1 for p in r.print_parts)


def _swivel_parts(tmpl):
    v = tmpl.defaults()
    r = tmpl.build(v)
    a = {p.name: p.solid for p in r.assembled}
    xc = -v["bend_radius"] + v["ring_opening"] / 2 + 6
    return a["Inner ring (turns)"], a["Outer ring (hangs)"], xc


def _collides(a, b):
    return (a ^ b).volume() > 1e-6


def test_swivel_prints_with_clearance_and_cannot_fall_out(tmpl):
    inner, outer, _ = _swivel_parts(tmpl)
    assert inner.min_gap(outer, 5) >= 0.49  # print-in-place gap
    assert not _collides(inner.translate([0, 0, 1.0]), outer)  # lifts to clear the clicks
    assert _collides(inner.translate([0, 0, 1.5]), outer)  # but is captured
    assert _collides(inner.translate([0, 0, -1.5]), outer)


def test_swivel_clicks_into_positions(tmpl):
    inner, outer, xc = _swivel_parts(tmpl)

    def drop(m):
        d = 0.0
        while d < 3 and not _collides(m.translate([0, 0, -(d + 0.02)]), outer):
            d += 0.02
        return d

    between = inner.translate([-xc, 0, 0]).rotate([0, 0, 22.5]).translate([xc, 0, 0])
    assert drop(inner) - drop(between) >= 0.3  # settles noticeably deeper at a click


def test_plate_layout_without_overlap(result):
    from modelbuilder.templates.base import PLATE_SPACING

    pitch = 256 + PLATE_SPACING
    plates = set()
    for p in result.print_parts:
        b = p.solid.bounding_box()
        k = int(b[0] // pitch)
        plates.add(k)
        x0 = k * pitch
        assert b[0] >= x0 and b[3] <= x0 + 256 and b[1] >= 0 and b[4] <= 256, p.name
        assert b[2] == pytest.approx(0, abs=1e-6), p.name
    assert len(plates) <= 2
    for a, b in itertools.combinations(result.print_parts, 2):
        assert (a.solid ^ b.solid).volume() == pytest.approx(0, abs=1e-6)


def test_light(result):
    total = sum(p.solid.volume() for p in result.print_parts)
    assert total < 100_000  # under 100 cm^3


def test_ball_fits_channel(tmpl):
    v = tmpl.defaults()
    _, _, geo = tmpl._chute(v)
    assert geo["w_in"] > v["ball_diameter"] + 4  # side to side clearance
    assert geo["depth"] > v["ball_diameter"] / 2  # side panels reach past the ball's centre


def test_halves_print_flat_and_short(tmpl):
    v = tmpl.defaults()
    half, full, geo = tmpl._chute(v)
    b = half.bounding_box()
    assert b[2] == pytest.approx(0, abs=1e-6)
    assert b[5] - b[2] < 60  # low and stable, sitting on its side panel
    # Footprint: the first layer is the whole side panel, not a thin edge.
    first_layer = half.slice(0.1).area()
    assert first_layer > 3000  # mm^2
    assert len(full.decompose()) == 1  # the two halves meet into one chute


def test_small_bed_overflows_to_second_plate(tmpl):
    r = tmpl.build(tmpl.defaults() | {"bed_size": 180})
    assert any(n.startswith("Needs") for n in r.notes)


@pytest.mark.parametrize("ball", [45, 67, 100])
def test_ball_sizes_build(tmpl, ball, tmp_path):
    r = tmpl.build(tmpl.defaults() | {"ball_diameter": ball})
    for p in r.print_parts:
        assert len(p.solid.decompose()) == (2 if p.name.startswith("Swivel") else 1), p.name
    write_3mf(str(tmp_path / "x.3mf"), [p.to_mesh() for p in r.print_parts])


def _steep_overhangs(solid):
    from modelbuilder.templates.base import Part

    m = Part("x", solid).to_mesh()
    tris = m.vertices[m.triangles]
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    length = np.linalg.norm(n, axis=1, keepdims=True)
    keep = length[:, 0] > 1e-9  # skip zero-area slivers
    tris, n = tris[keep], n[keep] / length[keep]
    # Faces pointing down steeper than 45 degrees that are not resting on the plate.
    return tris[(n[:, 2] < -0.71) & (tris[:, :, 2].min(axis=1) > 0.2)]


@pytest.mark.parametrize("angle", [45, 70, 90])
def test_prints_without_supports(tmpl, angle):
    r = tmpl.build(tmpl.defaults() | {"bend_angle": angle})
    for p in r.print_parts:
        bad = _steep_overhangs(p.solid)
        if len(bad):
            # Only short bridges (slot and tie-hole tops) are allowed.
            extent = (bad[:, :, :2].max(axis=1) - bad[:, :, :2].min(axis=1)).max()
            assert extent <= 10.5, f"{p.name}: {extent:.1f} mm unsupported span"


@pytest.mark.parametrize("angle", [30, 60, 90])
def test_bend_angles_build_one_piece(tmpl, angle):
    r = tmpl.build(tmpl.defaults() | {"bend_angle": angle})
    assert len(r.print_parts[0].solid.decompose()) == 1


def test_rim_hook_option(tmpl):
    r = tmpl.build(tmpl.defaults() | {"mount": 0})
    names = [p.name for p in r.print_parts]
    assert sum(n.startswith("Hook") for n in names) == 4 and "Hanger" not in names


def test_hanger_fits_block_and_clears_chute(tmpl):
    v = tmpl.defaults()
    r = tmpl.build(v)
    a = {p.name: p.solid for p in r.assembled}
    hanger, block = a["Hanger"], a["Rim block"]
    assert (hanger ^ block).volume() == pytest.approx(0, abs=1e-6)
    assert hanger.min_gap(block, 2) == pytest.approx(0.4, abs=0.05)  # snug cap
    xc = -v["bend_radius"] + v["ring_opening"] / 2 + 6
    for ang in range(0, 360, 45):  # every click position
        c = a["Chute"].translate([-xc, 0, 0]).rotate([0, 0, ang]).translate([xc, 0, 0])
        assert hanger.min_gap(c, 10) > 2
    i, o = a["Inner ring (turns)"], a["Outer ring (hangs)"]
    assert hanger.min_gap(i, 5) > 1  # the turning ring never rubs the hanger
