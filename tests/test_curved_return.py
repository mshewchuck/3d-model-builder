import itertools

import numpy as np
import pytest
from manifold3d import Manifold

from modelbuilder.templates import CurvedReturnTemplate
from modelbuilder.templates.base import PLATE_SPACING, Part
from modelbuilder.threemf import write_3mf


@pytest.fixture(scope="module")
def tmpl():
    return CurvedReturnTemplate()


@pytest.fixture(scope="module")
def result(tmpl):
    return tmpl.build(tmpl.defaults())


def _assembled(result):
    return {p.name: p.solid for p in result.assembled}


def test_parts(result):
    names = [p.name for p in result.print_parts]
    assert names == ["Chute half A", "Chute half B", "Hanger"]
    for p in result.print_parts:
        assert len(p.solid.decompose()) == 1, p.name


def test_defaults_fit_one_plate_without_overlap(result):
    assert not any(n.startswith("Needs") for n in result.notes)
    for p in result.print_parts:
        b = p.solid.bounding_box()
        assert b[0] >= 0 and b[1] >= 0 and b[3] <= 256 and b[4] <= 256, p.name
        assert b[2] == pytest.approx(0, abs=1e-6), p.name
    for a, b in itertools.combinations(result.print_parts, 2):
        assert (a.solid ^ b.solid).volume() == pytest.approx(0, abs=1e-6)


def test_small_bed_uses_more_plates(tmpl):
    r = tmpl.build(tmpl.defaults() | {"bed_size": 180})
    assert any(n.startswith("Needs") for n in r.notes)
    # The hanger (about 197 mm long) cannot fit a 180 mm bed at the default drop: warn about it.
    assert any(n.startswith("Warning: the hanger") for n in r.notes)
    pitch = 180 + PLATE_SPACING
    for p in r.print_parts:
        if p.name == "Hanger":
            continue
        b = p.solid.bounding_box()
        x0 = int(b[0] // pitch) * pitch
        assert b[3] <= x0 + 180 and b[4] <= 180, p.name


def test_light(result):
    assert sum(p.solid.volume() for p in result.print_parts) < 95_000  # under 95 cm^3


def test_ball_fits_channel(tmpl):
    v = tmpl.defaults()
    _, _, geo = tmpl._chute(v)
    assert geo["w_in"] > v["ball_diameter"] + 4
    assert geo["depth"] > v["ball_diameter"] / 2


def test_halves_print_flat_and_short(tmpl):
    half, full, _ = tmpl._chute(tmpl.defaults())
    b = half.bounding_box()
    assert b[2] == pytest.approx(0, abs=1e-6)
    assert b[5] - b[2] < 60
    assert half.slice(0.1).area() > 3000  # first layer is the whole side panel
    assert len(full.decompose()) == 1


def _steep_overhangs(solid):
    m = Part("x", solid).to_mesh()
    tris = m.vertices[m.triangles]
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    length = np.linalg.norm(n, axis=1, keepdims=True)
    keep = length[:, 0] > 1e-9
    tris, n = tris[keep], n[keep] / length[keep]
    return tris[(n[:, 2] < -0.71) & (tris[:, :, 2].min(axis=1) > 0.2)]


@pytest.mark.parametrize("angle", [45, 70, 90])
def test_prints_without_supports(tmpl, angle):
    r = tmpl.build(tmpl.defaults() | {"bend_angle": angle})
    for p in r.print_parts:
        bad = _steep_overhangs(p.solid)
        if len(bad):
            extent = (bad[:, :, :2].max(axis=1) - bad[:, :, :2].min(axis=1)).max()
            assert extent <= 10.5, f"{p.name}: {extent:.1f} mm unsupported span"


@pytest.mark.parametrize("angle", [30, 60, 90])
def test_bend_angles_build(tmpl, angle):
    r = tmpl.build(tmpl.defaults() | {"bend_angle": angle})
    assert all(len(p.solid.decompose()) == 1 for p in r.print_parts)


@pytest.mark.parametrize("ball", [45, 67, 100])
def test_ball_sizes_build(tmpl, ball, tmp_path):
    r = tmpl.build(tmpl.defaults() | {"ball_diameter": ball})
    assert all(len(p.solid.decompose()) == 1 for p in r.print_parts)
    write_3mf(str(tmp_path / "x.3mf"), [p.to_mesh() for p in r.print_parts])


def test_hanger_caps_block_and_meets_chute(tmpl, result):
    a = _assembled(result)
    hanger, block, chute = a["Hanger"], a["Rim block"], a["Chute"]
    assert (hanger ^ block).volume() == pytest.approx(0, abs=1e-6)
    assert hanger.min_gap(block, 2) == pytest.approx(0.4, abs=0.05)  # snug cap
    assert (hanger ^ chute).volume() == pytest.approx(0, abs=1e-3)  # touches, never overlaps
    assert hanger.min_gap(chute, 1) < 0.01  # plate sits flat on the back of the floor


def test_screws_pass_through_hanger_and_chute(tmpl, result):
    v = tmpl.defaults()
    a = _assembled(result)
    z = v["lead_in"] - 6
    x_plate = -(v["bend_radius"] + v["wall"]) - 4
    for y in (18, -18):
        rod = Manifold.cylinder(30, 1.2, circular_segments=12).rotate([0, 90, 0]).translate([x_plate - 6.5, y, z])
        assert (rod ^ a["Hanger"]).volume() == pytest.approx(0, abs=1e-6)
        assert (rod ^ a["Chute"]).volume() == pytest.approx(0, abs=1e-6)


def test_short_board_distance_rejected(tmpl):
    with pytest.raises(ValueError):
        tmpl.build(tmpl.defaults() | {"board_to_center": 60})
