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
    assert names == ["Chute", "Hanger"]
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
    assert not any(n.startswith("Warning") for n in r.notes)  # every part fits a 180 mm bed
    for a, b in itertools.combinations(r.print_parts, 2):
        assert (a.solid ^ b.solid).volume() == pytest.approx(0, abs=1e-6)
    pitch = 180 + PLATE_SPACING
    for p in r.print_parts:
        b = p.solid.bounding_box()
        x0 = int(b[0] // pitch) * pitch
        assert b[3] <= x0 + 180 and b[4] <= 180, p.name


def test_light(result):
    assert sum(p.solid.volume() for p in result.print_parts) < 105_000  # under 105 cm^3


def test_ball_fits_channel(tmpl):
    v = tmpl.defaults()
    _, _, geo = tmpl._chute(v | {"bend_radius": 70})
    assert geo["w_in"] > v["ball_diameter"] + 4
    assert geo["depth"] > v["ball_diameter"] / 2


def test_halves_print_flat_and_short(tmpl):
    half, full, _ = tmpl._chute(tmpl.defaults() | {"bend_radius": 100})
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


def _cut_chute(tmpl, r):
    """Do what the user does in the slicer: cut the exported chute at half its height and flip
    the upper piece onto its side panel. Returns the two pieces as printed."""
    chute = next(p.solid for p in r.print_parts if p.name == "Chute")
    zc = chute.bounding_box()[5] / 2
    lower, upper = chute.split_by_plane([0, 0, 1], zc)  # (above, below) order checked below
    if lower.bounding_box()[2] > 1:
        lower, upper = upper, lower
    b = upper.bounding_box()
    upper = upper.mirror([0, 0, 1]).translate([0, 0, b[5]])
    return lower, upper


def test_chute_cuts_into_two_identical_flat_halves(tmpl, result):
    lower, upper = _cut_chute(tmpl, result)
    v = tmpl.defaults()
    half, _, _ = tmpl._chute(v | {"bend_radius": tmpl.auto_bend_radius(v)})
    for piece in (lower, upper):
        assert len(piece.decompose()) == 1
        assert piece.bounding_box()[2] == pytest.approx(0, abs=1e-6)
        assert piece.volume() == pytest.approx(half.volume(), rel=1e-3)
        assert piece.slice(0.1).area() > 3000  # lies on its whole side panel


@pytest.mark.parametrize("angle", [45, 70, 90])
def test_prints_without_supports(tmpl, angle):
    r = tmpl.build(tmpl.defaults() | {"bend_angle": angle})
    pieces = [Part(f"Chute half {i}", p) for i, p in enumerate(_cut_chute(tmpl, r))]
    pieces += [p for p in r.print_parts if p.name != "Chute"]
    for p in pieces:
        bad = _steep_overhangs(p.solid)
        if len(bad):
            # A slicer bridges each flat overhang across its short side, so the bridge length is
            # the smaller of each face's two extents. Allow up to about 10 mm.
            ext = bad[:, :, :2].max(axis=1) - bad[:, :, :2].min(axis=1)
            span = ext.min(axis=1).max()
            assert span <= 10.5, f"{p.name}: {span:.1f} mm unsupported bridge"


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
    v = tmpl.defaults()
    a = _assembled(result)
    hanger, block, chute = a["Hanger"], a["Rim block"], a["Chute"]
    assert (hanger ^ block).volume() == pytest.approx(0, abs=1e-6)
    assert hanger.min_gap(block, 2) == pytest.approx(0.4, abs=0.05)  # snug cap
    assert (hanger ^ chute).volume() == pytest.approx(0, abs=1e-3)
    assert hanger.min_gap(chute, 1) < 0.01  # block sits flat on the back of the chute
    # The chute floor stands off the backboard by the set gap (its joining ears, 6 mm deep,
    # sit a little closer) and nothing touches the board except the hanger.
    board_x = a["Backboard"].bounding_box()[3]
    x_floor = -(tmpl.auto_bend_radius(v) + v["wall"])
    assert x_floor - board_x == pytest.approx(v["standoff"], abs=0.01)
    assert chute.bounding_box()[0] - board_x > v["standoff"] - 6.5


def test_screws_go_through_chute_into_block(tmpl, result):
    v = tmpl.defaults()
    a = _assembled(result)
    x_floor = -(tmpl.auto_bend_radius(v) + v["wall"])
    for y in (18, -18):
        for d in (6, 18):
            z = v["lead_in"] - d
            rod = Manifold.cylinder(14, 1.2, circular_segments=12).rotate([0, 90, 0]).translate([x_floor - 12, y, z])
            assert (rod ^ a["Hanger"]).volume() == pytest.approx(0, abs=1e-6)  # pilot hole
            assert (rod ^ a["Chute"]).volume() == pytest.approx(0, abs=1e-6)  # clearance hole
            fat = Manifold.cylinder(10, 2.0, circular_segments=12).rotate([0, 90, 0]).translate([x_floor - 10, y, z])
            assert (fat ^ a["Hanger"]).volume() > 0  # solid plastic around it to thread into


def test_spout_stays_inside_rim(result):
    assert any(n.startswith("The spout reaches") for n in result.notes)


def test_long_spout_warns(tmpl):
    r = tmpl.build(tmpl.defaults() | {"bend_radius": 140, "exit_length": 120})
    assert any("past the front of the rim" in n for n in r.notes)


def test_short_board_distance_rejected(tmpl):
    with pytest.raises(ValueError):
        tmpl.build(tmpl.defaults() | {"board_to_center": 60, "standoff": 60})


def test_ball_lands_on_the_chute(tmpl):
    """Drop the ball straight down from the rim centre: it must hit the chute floor."""
    for kw in ({}, {"standoff": 40}, {"board_to_center": 90}, {"ball_diameter": 67}):
        v = tmpl.defaults() | kw
        r = tmpl.build(v)
        assert not any("could miss" in n for n in r.notes), kw
        a = _assembled(r)
        board_x = a["Backboard"].bounding_box()[3]
        x = board_x + v["board_to_center"]
        ball = Manifold.sphere(v["ball_diameter"] / 2, 32)
        z = v["lead_in"] + 50
        while z > -400 and (ball.translate([x, 0, z]) ^ a["Chute"]).volume() < 1:
            z -= 2
        assert z > -400, f"ball fell past the chute {kw}"
        hit = ball.translate([x, 0, z]) ^ a["Chute"]
        hb = hit.bounding_box()
        # it lands on the floor (low in the ball), not on the top edge of a side panel
        assert hb[5] < z + 0.2 * v["ball_diameter"], kw


def test_small_bend_warns_ball_could_miss(tmpl):
    r = tmpl.build(tmpl.defaults() | {"bend_radius": 60})
    assert any("could miss" in n for n in r.notes)
