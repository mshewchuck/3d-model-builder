import xml.etree.ElementTree as ET
import zipfile

import pytest

from modelbuilder.templates import TEMPLATES, BallReturnTemplate
from modelbuilder.templates.base import plate_footprint
from modelbuilder.threemf import write_3mf

NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


@pytest.fixture(scope="module")
def result():
    t = BallReturnTemplate()
    return t.build(t.defaults())


def test_every_part_is_one_solid_piece(result):
    for part in result.assembled + result.print_parts:
        assert not part.solid.is_empty(), part.name
        assert len(part.solid.decompose()) == 1, part.name
        assert part.solid.volume() > 0, part.name


def test_defaults_fit_bambu_plate(result):
    fx, fy, fz = plate_footprint(result.print_parts)
    assert max(fx, fy) <= 256 and fz <= 256
    for part in result.print_parts:
        assert part.solid.bounding_box()[2] == pytest.approx(0, abs=1e-6), part.name
    assert not any(n.startswith("Warning") for n in result.notes)


def test_oversize_settings_warn():
    t = BallReturnTemplate()
    v = t.defaults() | {"ball_diameter": 240, "clearance": 25, "bed_size": 180}
    assert any(n.startswith("Warning") for n in t.build(v).notes)


def test_validation_rejects_out_of_range():
    t = BallReturnTemplate()
    assert t.validate(t.defaults()) == []
    assert t.validate(t.defaults() | {"rail_height": 500})


@pytest.mark.parametrize("ball", [127, 178])
def test_common_ball_sizes_build(ball):
    t = BallReturnTemplate()
    r = t.build(t.defaults() | {"ball_diameter": ball})
    assert all(len(p.solid.decompose()) == 1 for p in r.print_parts)


def test_3mf_package_is_valid(result, tmp_path):
    path = tmp_path / "out.3mf"
    meshes = [p.to_mesh() for p in result.print_parts]
    write_3mf(str(path), meshes, title="Test")
    with zipfile.ZipFile(path) as z:
        assert {"[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model"} <= set(z.namelist())
        root = ET.fromstring(z.read("3D/3dmodel.model"))
    assert root.get("unit") == "millimeter"
    objects = root.findall("m:resources/m:object", NS)
    assert len(objects) == len(meshes) == len(root.findall("m:build/m:item", NS))
    for obj, mesh in zip(objects, meshes):
        tris = obj.findall("m:mesh/m:triangles/m:triangle", NS)
        verts = obj.findall("m:mesh/m:vertices/m:vertex", NS)
        assert len(tris) == len(mesh.triangles) and len(verts) == len(mesh.vertices)
        n = len(verts)
        assert all(0 <= int(t.get(k)) < n for t in tris for k in ("v1", "v2", "v3"))


def test_registry_has_templates():
    assert TEMPLATES and all(t.params for t in TEMPLATES)


def test_single_part_and_light():
    t = BallReturnTemplate()
    r = t.build(t.defaults())
    assert len(r.print_parts) == 1
    solid = r.print_parts[0].solid
    without = t.build(t.defaults() | {"cutouts": 0}).print_parts[0].solid
    assert solid.volume() < 0.8 * without.volume()
    assert solid.volume() < 100_000  # under 100 cm^3 of plastic
