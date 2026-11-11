"""Template framework: a template is a set of parameters plus a build function."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from manifold3d import Manifold

from ..threemf import Mesh


@dataclass
class Param:
    key: str
    label: str
    default: float
    minimum: float
    maximum: float
    unit: str = "mm"
    help: str = ""


@dataclass
class Part:
    name: str
    solid: Manifold
    color: str = "#e07b39"

    def to_mesh(self) -> Mesh:
        m = self.solid.to_mesh()
        verts = np.asarray(m.vert_properties)[:, :3]
        tris = np.asarray(m.tri_verts)
        return Mesh(self.name, verts, tris)

    def size(self) -> tuple[float, float, float]:
        b = self.solid.bounding_box()
        return (b[3] - b[0], b[4] - b[1], b[5] - b[2])


@dataclass
class BuildResult:
    assembled: list[Part]  # how it looks installed (for the preview)
    print_parts: list[Part]  # laid out on the build plate (for export)
    notes: list[str] = field(default_factory=list)


class Template:
    name: str = ""
    description: str = ""
    params: list[Param] = []

    def defaults(self) -> dict[str, float]:
        return {p.key: p.default for p in self.params}

    def validate(self, values: dict[str, float]) -> list[str]:
        errors = []
        for p in self.params:
            v = values.get(p.key)
            if v is None:
                errors.append(f"{p.label}: missing")
            elif not (p.minimum <= v <= p.maximum):
                errors.append(f"{p.label}: must be between {p.minimum:g} and {p.maximum:g} {p.unit}")
        return errors

    def build(self, values: dict[str, float]) -> BuildResult:
        raise NotImplementedError


def lay_out_on_plate(parts: list[Part], gap: float = 10.0) -> list[Part]:
    """Drop each part onto z=0 and place them side by side along X, centred at the origin."""
    placed = []
    x_cursor = 0.0
    for part in parts:
        b = part.solid.bounding_box()
        solid = part.solid.translate([x_cursor - b[0], -(b[1] + b[4]) / 2, -b[2]])
        x_cursor += (b[3] - b[0]) + gap
        placed.append(Part(part.name, solid, part.color))
    total = x_cursor - gap
    return [Part(p.name, p.solid.translate([-total / 2, 0, 0]), p.color) for p in placed]


def plate_footprint(parts: list[Part]) -> tuple[float, float, float]:
    xs, ys, zs = [], [], []
    for p in parts:
        b = p.solid.bounding_box()
        xs += [b[0], b[3]]
        ys += [b[1], b[4]]
        zs += [b[2], b[5]]
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
