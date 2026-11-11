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
    assert names.count("Chute") == 1
    assert sum(n.startswith("Swivel ring") for n in names) == 1
    assert sum(n.startswith("Hook") for n in names) == 4
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


def test_defaults_fit_one_bambu_plate_without_overlap(result):
    assert not any(n.startswith("Not everything") for n in result.notes)
    for p in result.print_parts:
        b = p.solid.bounding_box()
        assert b[0] >= 0 and b[1] >= 0 and b[3] <= 256 and b[4] <= 256, p.name
        assert b[2] == pytest.approx(0, abs=1e-6), p.name
    for a, b in itertools.combinations(result.print_parts, 2):
        assert (a.solid ^ b.solid).volume() == pytest.approx(0, abs=1e-6)


def test_light(result):
    total = sum(p.solid.volume() for p in result.print_parts)
    assert total < 100_000  # under 100 cm^3


def test_ball_fits_trough(tmpl):
    v = tmpl.defaults()
    _, geo = tmpl._chute(v)
    r = v["ball_diameter"] / 2
    # Ball resting on the floor centre must clear the 45 degree lips.
    half = geo["wf"] / 2
    dist_to_lip = abs(-r - half) / 2 ** 0.5
    assert dist_to_lip > r


def test_small_bed_overflows_to_second_plate(tmpl):
    r = tmpl.build(tmpl.defaults() | {"bed_size": 150})
    assert any(n.startswith("Not everything") for n in r.notes)


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
