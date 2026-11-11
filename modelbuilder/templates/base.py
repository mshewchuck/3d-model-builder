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


def pack_on_plate(parts: list[Part], bed: float, gap: float = 5.0, margin: float = 3.0) -> tuple[list[Part], bool]:
    """Try a few packing orders and keep the first that fits on one plate."""
    keys = [
        lambda p: -p.size()[1],
        lambda p: -p.size()[0] * p.size()[1],
        lambda p: -p.size()[0],
    ]
    result = None
    for key in keys:
        order = sorted(range(len(parts)), key=lambda i: key(parts[i]))
        result = _shelf_pack(parts, order, bed, gap, margin)
        if result[1]:
            return result
    return result


def _shelf_pack(parts, order, bed, gap, margin):
    """Shelf-pack parts onto a square bed (origin at the plate corner, like Bambu printers).

    Returns the placed parts and whether everything fit on one plate. Parts that do not fit
    are placed to the right of the plate so Bambu Studio's Arrange can move them to plate 2.
    """
    placed: list[Part | None] = [None] * len(parts)
    x = y = margin
    row_h = 0.0
    fits = True
    overflow_x = bed + 20
    for i in order:
        p = parts[i]
        sx, sy, _ = p.size()
        if x + sx > bed - margin and x > margin:  # new row
            x, y = margin, y + row_h + gap
            row_h = 0.0
        b = p.solid.bounding_box()
        if y + sy > bed - margin or sx > bed - 2 * margin:
            fits = False
            dest = (overflow_x, margin)
            overflow_x += sx + gap
        else:
            dest = (x, y)
            x += sx + gap
            row_h = max(row_h, sy)
        placed[i] = Part(p.name, p.solid.translate([dest[0] - b[0], dest[1] - b[1], -b[2]]), p.color)
    return placed, fits
