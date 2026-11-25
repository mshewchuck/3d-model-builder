"""Serve Meters 505 fridge magnet: the "Classic Dial" design.

A round meter face: blue rim, white face, the Serve Meters logo, a gauge with a
green arc, the logo's green rising arrow as the needle, and the branch number.

Layers, bottom to top (print face up, no supports):
* Blue body: the full disc, including the rim, up to the top of the face.
* White face: an inlay flush with the rim, with holes where the details go.
* Blue details and green details: they fill those holes and stand RAISED above the face.
* Magnet pocket(s) in the back, opening on the plate side (its roof is a short bridge).

Each colour is its own part of one object, so in Bambu Studio you pick a filament
per part. The artwork is drawn on a 200 x 200 unit canvas (the same one as the 2D
concepts) and scaled to the chosen diameter.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, FillRule, Manifold

from .base import BuildResult, Param, Part, Template, pack_on_plate

BLUE = "#0054a5"  # Serve blue, sampled from the logo
GREEN = "#72bf44"  # Serve green
WHITE = "#f4f4f4"
LOGO_PNG = Path(__file__).resolve().parent.parent / "assets" / "serve_meters_logo.png"
SEG = 128


def _cs(polys) -> CrossSection:
    """CrossSection from rings (outer and holes) using even-odd filling."""
    return CrossSection([np.asarray(p, dtype=float) for p in polys if len(p) >= 3], FillRule.EvenOdd)


def _stadium(x0, y0, x1, y1, w) -> CrossSection:
    """A rounded bar from (x0, y0) to (x1, y1), w wide."""
    return CrossSection.batch_hull([CrossSection.circle(w / 2, 24).translate([x0, y0]),
                                    CrossSection.circle(w / 2, 24).translate([x1, y1])])


def _logo_shapes(units_x, units_y, units_w):
    """Trace the logo PNG into blue and green shapes in canvas units (y down).

    Leaves out the trademark symbol, which is far too small to print.
    """
    import contourpy
    from PIL import Image

    im = np.asarray(Image.open(LOGO_PNG).convert("RGBA")).astype(float) / 255.0
    h, w = im.shape[:2]
    alpha = im[..., 3]
    green = im[..., 1] > im[..., 2] + 0.08
    out = {}
    for name, mask in (("blue", ~green), ("green", green)):
        z = np.pad(np.where(mask, alpha, 0.0), 2)  # pad so every outline closes
        rings = contourpy.contour_generator(z=z).lines(0.5)
        keep = []
        for ring in rings:
            px, py = ring[:, 0] - 2, ring[:, 1] - 2
            # the trademark symbol: small marks in the top-right corner
            if px.min() > 0.9 * w and py.max() < 0.3 * h:
                continue
            s = units_w / w
            keep.append(np.column_stack([units_x + px * s, units_y + py * s]))
        out[name] = _cs(keep).simplify(0.05)
    return out


def _text(s, cx, baseline, height):
    """Outline of text, centred on cx, in canvas units (y down)."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath

    import logging

    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    for family in ("Inter Black", "Arial Black", "DejaVu Sans"):
        prop = FontProperties(family=family, weight="bold")
        try:
            path = TextPath((0, 0), s, size=100, prop=prop)
            break
        except Exception:  # font missing: try the next one
            continue
    polys = path.to_polygons()
    pts = np.vstack(polys)
    x0, x1 = pts[:, 0].min(), pts[:, 0].max()
    cap = pts[:, 1].max()
    k = height / cap
    return _cs([np.column_stack([cx + (p[:, 0] - (x0 + x1) / 2) * k, baseline - p[:, 1] * k]) for p in polys])


def _arc_band(cx, cy, r, a0, a1, w) -> CrossSection:
    """A band along a circular arc (angles in degrees, counter-clockwise, y up) with round ends."""
    n = 48
    pts_out, pts_in = [], []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts_out.append((cx + (r + w / 2) * math.cos(a), cy - (r + w / 2) * math.sin(a)))
        pts_in.append((cx + (r - w / 2) * math.cos(a), cy - (r - w / 2) * math.sin(a)))
    band = _cs([pts_out + pts_in[::-1]])
    for a in (a0, a1):
        ar = math.radians(a)
        band = band + CrossSection.circle(w / 2, 24).translate([cx + r * math.cos(ar), cy - r * math.sin(ar)])
    return band


def _arrow(x0, y0, x1, y1, w, head=2.2) -> CrossSection:
    """The logo's rising arrow: a thick shaft and a triangular head (canvas units)."""
    a = math.atan2(y1 - y0, x1 - x0)
    hl, hw = w * head, w * head * 0.95
    bx, by = x1 - hl * math.cos(a), y1 - hl * math.sin(a)
    px, py = -math.sin(a), math.cos(a)
    shaft = _stadium(x0, y0, bx + 0.5 * math.cos(a), by + 0.5 * math.sin(a), w)
    tip = _cs([[(x1, y1), (bx + px * hw / 2, by + py * hw / 2), (bx - px * hw / 2, by - py * hw / 2)]])
    return shaft + tip


class DialMagnetTemplate(Template):
    name = "Serve Meters dial magnet"
    single_object = True  # one object, one part per colour
    description = (
        "Round fridge magnet in Serve colours: meter face with the Serve Meters logo, a gauge, "
        "the green arrow as the needle and the branch number. Each colour is its own part."
    )
    params = [
        Param("diameter", "Magnet diameter", 80, 50, 150,
              help="80 mm or more keeps the logo's thinnest lettering at least 0.6 mm wide, so a 0.4 mm nozzle prints it cleanly."),
        Param("branch", "Branch number", 505, 0, 9999, unit="",
              help="The number printed on the face."),
        Param("magnet_d", "Magnet diameter (disc)", 12, 3, 40,
              help="The round magnets you'll glue in. 12 x 3 mm is a common size."),
        Param("magnet_t", "Magnet thickness", 3, 1, 10),
        Param("magnet_count", "Number of magnets", 1, 1, 3, unit="",
              help="1 in the middle, or 3 in a triangle for a stronger grip on a big magnet."),
        Param("magnet_fit", "Magnet pocket clearance", 0.2, 0, 1,
              help="Extra room around the magnet. 0.2 mm is a snug press fit; glue it either way."),
        Param("face_layer", "Face layer thickness", 0.8, 0.4, 2,
              help="Thickness of the white face inlay (and how deep the details sit in it)."),
        Param("raised", "Detail height above face", 0.4, 0, 1.6,
              help="How far the logo, gauge and number stand proud of the face. 0 makes it flush."),
    ]

    def artwork(self, v):
        """2D artwork in canvas units (200 x 200, y down): blue and green detail shapes."""
        logo = _logo_shapes(58, 44, 84)
        cx, cy = 100.0, 112.0
        blue = logo["blue"]
        for a0, a1 in ((200, 150), (30, -20)):  # gauge ticks on the sides, clear of the logo
            for a in np.linspace(a0, a1, 3):
                ar = math.radians(a)
                blue = blue + _stadium(cx + 58 * math.cos(ar), cy - 58 * math.sin(ar),
                                       cx + 66 * math.cos(ar), cy - 66 * math.sin(ar), 3.2)
        blue = blue + CrossSection.circle(7, 40).translate([cx, cy - 4])  # needle hub
        blue = blue + _text(str(int(v["branch"])), 100, 171, 27)
        green = logo["green"] + _arc_band(cx, cy, 70, 40, -20, 7)
        green = green + _arrow(100, 116, 140, 88, 5.2)
        green = green - blue  # where they touch (ticks over the arc, the hub over the needle), blue wins
        return blue, green

    def build(self, v: dict[str, float]) -> BuildResult:
        d = v["diameter"]
        k = d / 200.0  # mm per canvas unit

        def to_mm(cs: CrossSection) -> CrossSection:
            return cs.translate([-100, -100]).scale([k, -k])  # canvas y down -> mm y up, centred

        r = d / 2
        r_face = 82 * k  # white face inside the blue rim
        pocket_d = v["magnet_d"] + 2 * v["magnet_fit"]
        pocket_h = v["magnet_t"] + 0.2
        base_t = max(2.0, pocket_h + 0.8)  # keep at least 0.8 mm of plastic over the magnet
        face_t = v["face_layer"]
        top = base_t + face_t  # top of the rim and of the white face
        raised = v["raised"]

        blue2d, green2d = (to_mm(c) for c in self.artwork(v))
        details2d = blue2d + green2d
        face2d = CrossSection.circle(r_face, SEG)
        blue2d = blue2d ^ face2d
        green2d = green2d ^ face2d

        body = Manifold.cylinder(top, r, circular_segments=SEG)
        body = body - Manifold.cylinder(face_t + 1, r_face, circular_segments=SEG).translate([0, 0, base_t])
        # Magnet pocket(s), open on the plate side.
        if v["magnet_count"] < 2:
            spots = [(0.0, 0.0)]
        else:
            n = int(v["magnet_count"])
            rr = min(r * 0.45, r_face - pocket_d)
            spots = [(rr * math.cos(math.radians(90 + 360 * i / n)), rr * math.sin(math.radians(90 + 360 * i / n)))
                     for i in range(n)]
        for x, y in spots:
            body = body - Manifold.cylinder(pocket_h + 0.01, pocket_d / 2, circular_segments=64).translate(
                [x, y, -0.01])

        face = Manifold.extrude(face2d - details2d, face_t).translate([0, 0, base_t])
        blue_detail = Manifold.extrude(blue2d, face_t + raised).translate([0, 0, base_t])
        green_detail = Manifold.extrude(green2d, face_t + raised).translate([0, 0, base_t])

        parts = [
            Part("Blue - body and rim", body, BLUE),
            Part("White - face", face, WHITE),
            Part("Blue - logo, gauge and number", blue_detail, BLUE),
            Part("Green - logo arrow, gauge arc and needle", green_detail, GREEN),
        ]
        placed, _ = pack_on_plate([Part("Magnet", body + face + blue_detail + green_detail, BLUE)], 256)
        b = placed[0].solid.bounding_box()
        o = parts[0].solid.bounding_box()
        shift = [b[0] - o[0], b[1] - o[1], 0]  # same offset for every part keeps them aligned
        print_parts = [Part(p.name, p.solid.translate(shift), p.color) for p in parts]

        notes = [
            f"{d:.0f} mm across, {top + raised:.1f} mm thick. The details stand {raised:.1f} mm proud of the face.",
            "Bambu Studio: the file is one object with 4 parts. In the object list, set the parts "
            "named Blue to your blue filament, White to white, and Green to green. Print face up, "
            "with supports off.",
            f"Magnet: {int(v['magnet_count'])} x {v['magnet_d']:g} x {v['magnet_t']:g} mm disc"
            f"{'s' if v['magnet_count'] >= 2 else ''}. The pocket is {pocket_d:.1f} mm wide and "
            f"{pocket_h:.1f} mm deep. Press it in and add a drop of CA glue.",
            "The ™ mark is left off: at this size it would be about 1 mm tall, too small to print.",
        ]
        return BuildResult(parts, print_parts, notes)
