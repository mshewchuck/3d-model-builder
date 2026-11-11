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


PLATE_SPACING = 30.0  # gap between plates laid side by side along +X


def pack_plates(parts: list[Part], bed: float, gap: float = 5.0, margin: float = 3.0):
    """Pack parts onto as few square plates as possible (origin at the plate corner, like
    Bambu printers). Plate k sits k * (bed + PLATE_SPACING) along +X, so in Bambu Studio
    Arrange (or "add plate") can drop them onto separate plates.

    Returns (placed parts in the original order, number of plates).
    """
    keys = [
        lambda p: -p.size()[1],
        lambda p: -p.size()[0] * p.size()[1],
        lambda p: -p.size()[0],
        lambda p: -max(p.size()[:2]),
    ]
    best = None
    for key in keys:
        order = sorted(range(len(parts)), key=lambda i: key(parts[i]))
        result = _shelf_pack(parts, order, bed, gap, margin)
        if best is None or result[1] < best[1]:
            best = result
    return best


def pack_on_plate(parts: list[Part], bed: float, gap: float = 5.0, margin: float = 3.0) -> tuple[list[Part], bool]:
    """Pack parts; returns (placed parts, whether everything fit on one plate)."""
    placed, plates = pack_plates(parts, bed, gap, margin)
    return placed, plates == 1


def _shelf_pack(parts, order, bed, gap, margin):
    plates: list[dict] = []  # each: x, y, row_h
    placed: list[Part | None] = [None] * len(parts)

    def try_place(pl, sx, sy):
        x, y, row_h = pl["x"], pl["y"], pl["row_h"]
        if x + sx > bed - margin and x > margin:
            x, y, row_h = margin, y + row_h + gap, 0.0
        if x + sx > bed - margin or y + sy > bed - margin:
            return None
        pl.update(x=x + sx + gap, y=y, row_h=max(row_h, sy))
        return x, y

    for i in order:
        p = parts[i]
        sx, sy, _ = p.size()
        spot = None
        for k, pl in enumerate(plates):
            xy = try_place(pl, sx, sy)
            if xy:
                spot = (k, xy)
                break
        if spot is None:
            plates.append(dict(x=margin, y=margin, row_h=0.0))
            xy = try_place(plates[-1], sx, sy)
            if xy is None:  # bigger than the bed: give it a plate of its own and close that plate
                xy = (margin, margin)
                plates[-1].update(y=bed)
            spot = (len(plates) - 1, xy)
        k, (x, y) = spot
        b = p.solid.bounding_box()
        ox = k * (bed + PLATE_SPACING)
        placed[i] = Part(p.name, p.solid.translate([ox + x - b[0], y - b[1], -b[2]]), p.color)
    return placed, len(plates)
