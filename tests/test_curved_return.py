import itertools

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
    assert names.count("Chute") == 1 and names.count("Ring") == 1
    assert sum(n.startswith("Hook") for n in names) == 4
    for p in result.print_parts:
        assert len(p.solid.decompose()) == 1, p.name


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
    assert all(len(p.solid.decompose()) == 1 for p in r.print_parts)
    write_3mf(str(tmp_path / "x.3mf"), [p.to_mesh() for p in r.print_parts])
