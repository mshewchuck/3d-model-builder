import itertools
import xml.etree.ElementTree as ET
import zipfile

import pytest
from manifold3d import JoinType, Manifold

from modelbuilder.templates import DialMagnetTemplate

NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


@pytest.fixture(scope="module")
def tmpl():
    return DialMagnetTemplate()


@pytest.fixture(scope="module")
def result(tmpl):
    return tmpl.build(tmpl.defaults())


def test_four_colour_parts_that_do_not_overlap(result):
    names = [p.name for p in result.print_parts]
    assert [n.split(" - ")[0] for n in names] == ["Blue", "White", "Blue", "Green"]
    for a, b in itertools.combinations(result.print_parts, 2):
        assert (a.solid ^ b.solid).volume() == pytest.approx(0, abs=1e-3), (a.name, b.name)
    whole = Manifold.batch_boolean([p.solid for p in result.print_parts], __import__("manifold3d").OpType.Add)
    assert len(whole.decompose()) == 1  # everything sits on the blue body: no loose bits


def test_size_layers_and_raised_details(tmpl, result):
    v = tmpl.defaults()
    body = result.assembled[0].solid.bounding_box()
    assert body[3] - body[0] == pytest.approx(v["diameter"], abs=0.1)
    top = body[5]
    face = result.assembled[1].solid.bounding_box()
    assert face[5] == pytest.approx(top)  # white face is flush with the rim
    for p in result.assembled[2:]:
        assert p.solid.bounding_box()[5] == pytest.approx(top + v["raised"])


def test_magnet_pocket(tmpl, result):
    v = tmpl.defaults()
    body = result.assembled[0].solid
    d = v["magnet_d"] + 2 * v["magnet_fit"]
    magnet = Manifold.cylinder(v["magnet_t"], v["magnet_d"] / 2, circular_segments=64)
    assert (magnet ^ body).volume() == pytest.approx(0, abs=1e-3)  # the magnet fits in its pocket
    snug = Manifold.cylinder(1, d / 2 + 0.3, circular_segments=64).translate([0, 0, 1])
    assert (snug ^ body).volume() > 0  # ...and the pocket isn't oversized
    roof = Manifold.cylinder(0.79, d / 2 - 0.5).translate([0, 0, v["magnet_t"] + 0.2 + 0.005])
    assert (roof - body).volume() == pytest.approx(0, abs=1e-3)  # at least 0.8 mm of plastic over it


def test_three_magnets(tmpl):
    r = tmpl.build(tmpl.defaults() | {"magnet_count": 3})
    body = r.assembled[0].solid
    v = tmpl.defaults()
    assert body.volume() < r.assembled[0].solid.volume() + 1
    full = Manifold.cylinder(v["magnet_t"], v["diameter"] / 2 - 1, circular_segments=96)
    missing = full - body
    assert len(missing.decompose()) == 3


def test_details_print_with_a_04_nozzle(tmpl):
    """Every logo/gauge/number stroke is at least 0.6 mm wide at the default 80 mm size."""
    v = tmpl.defaults()
    k = v["diameter"] / 200
    for cs in tmpl.artwork(v):
        cs = cs.scale([k, k])
        kept = cs.offset(-0.3, JoinType.Round).offset(0.3, JoinType.Round)
        assert kept.area() > 0.985 * cs.area()
        assert len(kept.decompose()) == len(cs.decompose())


def test_trademark_left_off(tmpl):
    blue, green = tmpl.artwork(tmpl.defaults())
    # The TM was at logo pixels x 412-437, y 31-44; the logo is drawn at x=58, y=44, 84 units wide.
    s = 84 / 438
    tm_zone = blue ^ __import__("manifold3d").CrossSection.square([25 * s, 13 * s]).translate(
        [58 + 412 * s, 44 + 31 * s])
    assert tm_zone.area() == pytest.approx(0, abs=0.01)


def test_branch_number_changes(tmpl):
    a = tmpl.artwork(tmpl.defaults())[0].area()
    b = tmpl.artwork(tmpl.defaults() | {"branch": 111})[0].area()
    assert a != pytest.approx(b, rel=0.01)


def test_exports_one_object_with_coloured_parts(tmpl, result, tmp_path):
    path = tmp_path / "magnet.3mf"
    tmpl.export(str(path), result)
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("3D/3dmodel.model"))
    items = root.findall("m:build/m:item", NS)
    assert len(items) == 1
    group = next(o for o in root.findall("m:resources/m:object", NS) if o.get("id") == items[0].get("objectid"))
    assert len(group.findall("m:components/m:component", NS)) == 4
    colors = {b.get("displaycolor") for b in root.findall("m:resources/m:basematerials/m:base", NS)}
    assert colors == {"#0054A5FF", "#72BF44FF", "#F4F4F4FF"}
