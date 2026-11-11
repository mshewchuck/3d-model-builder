"""Curved ball return in the style of store-bought hoop returns.

Parts (all print with no supports):
* Chute: a trough that bends 90 degrees, with a flat floor on the outside of
  the bend and two lips flared at 45 degrees. It prints lying on one lip, so
  the 45 degree lips and short window bridges need no supports. Floor slots
  and lip windows keep it light and give it the open-frame look.
* Ring: a flat collar that sits on top of the chute, where the ball drops in
  from the net. It has 4 cord holes and 3 pairs of zip-tie holes that line up
  with tie holes in the top of the chute.
* 4 hooks: flat J-hooks that hang on the rim tube with an eyelet for cord.

Frames: the chute is built lying on the bed (the "print frame") with the bend
centred on the Z axis. It enters along -Y and leaves along -X. `_to_installed`
maps it to the installed view: +Z up, the ball leaves toward +X.
"""

from __future__ import annotations

import math

from manifold3d import CrossSection, Manifold

from .base import BuildResult, Param, Part, Template, pack_on_plate

SEG = 96
CHUTE_COLOR = "#5b5f66"
RING_COLOR = "#f2c811"
HOOK_COLOR = "#2b2b2b"
RING_THICKNESS = 3.0
RING_BACK_GAP = 6.0  # ring opening starts this far in front of the floor
TIE_HOLE_R = 1.8


def _poly(points) -> CrossSection:
    """CrossSection from one polygon, in either winding order."""
    area = 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        area += x1 * y2 - x2 * y1
    return CrossSection([points if area > 0 else points[::-1]])


def _arc(cx, cy, r, a0, a1, n=48):
    return [
        (cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
         cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
        for i in range(n + 1)
    ]


class CurvedReturnTemplate(Template):
    name = "Curved ball return (store style)"
    description = (
        "Catch ring that hangs from the rim on 4 cords, with a curved open-frame chute that "
        "turns the ball and sends it back to you. Every part prints without supports."
    )
    params = [
        Param("ball_diameter", "Ball diameter", 67, 40, 130,
              help="Mini airless / tennis-ball size is about 65-70 mm."),
        Param("ring_opening", "Ring opening", 95, 60, 200,
              help="Inside diameter of the catch ring. A bit bigger than the bottom of your net."),
        Param("bend_radius", "Bend radius", 90, 50, 200,
              help="Radius of the chute's floor through the turn. Bigger turns more smoothly but is bigger to print."),
        Param("lead_in", "Straight section at top", 25, 10, 100),
        Param("exit_length", "Straight exit length", 50, 0, 150,
              help="Flat run after the turn that points the ball back at you."),
        Param("wall", "Wall thickness", 2.4, 1.6, 5),
        Param("rim_tube_diameter", "Rim tube diameter", 12, 4, 30,
              help="Thickness of the rim's metal tube. Sets the size of the hooks."),
        Param("bed_size", "Printer bed size", 256, 150, 400,
              help="256 for Bambu X1/P1/P2, 180 for the A1 mini."),
    ]

    # ------------------------------------------------------------------ chute
    def _chute(self, v):
        t = v["wall"]
        s = t / math.sqrt(2)
        ball = v["ball_diameter"]
        wf = 0.6 * ball  # floor width
        d = 0.55 * ball  # lip depth (radial)
        rf = v["bend_radius"]  # floor inner face radius
        a = d + s  # z of the floor's lower inner edge, so the lower lip touches z=0
        top = a + wf  # z of the floor's upper inner edge
        height = top + d + s

        floor = _poly([(rf, a - s), (rf + t, a - s), (rf + t, top + s), (rf, top + s)])
        lo_lip = _poly([(rf, a), (rf - d, a - d), (rf - d + s, a - d - s), (rf + s, a - s)])
        hi_lip = _poly([(rf, top), (rf + s, top + s), (rf - d + s, top + d + s), (rf - d, top + d)])
        corners = _poly([(rf, a), (rf + s, a - s), (rf + t, a - s), (rf + t, a)]) + _poly(
            [(rf, top), (rf + t, top), (rf + t, top + s), (rf + s, top + s)]
        )
        profile = floor + lo_lip + hi_lip + corners

        bend = Manifold.revolve(profile, SEG, 90)
        lead = Manifold.extrude(profile, v["lead_in"]).transform(
            [[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0]]
        )  # runs along -Y from the start of the bend
        chute = bend + lead
        exit_len = v["exit_length"]
        if exit_len > 0:
            ext = Manifold.extrude(profile, exit_len).translate([0, 0, -exit_len]).transform(
                [[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]]
            )  # runs along -X from the end of the bend
            chute = chute + ext

        # Floor slots across the path (8 mm wide, so the ball rolls straight over them).
        m = 7.0
        floor_cut = _poly([(rf - 1, a + m), (rf + t + 1, a + m), (rf + t + 1, top - m), (rf - 1, top - m)])
        slot_deg = math.degrees(8.0 / rf)
        pitch_deg = math.degrees(18.0 / rf)
        n = int((90 - 2 * pitch_deg) // pitch_deg)
        start = (90 - (n - 1) * pitch_deg - slot_deg) / 2
        slot = Manifold.revolve(floor_cut, 8, slot_deg)
        for i in range(n):
            chute = chute - slot.rotate([0, 0, start + i * pitch_deg])

        # Windows in the lips (the open-frame look). Lips are 45 degrees, so no supports.
        m2 = 7.0
        lip_cut = _poly([(rf - d + m2, -1), (rf - m2, -1), (rf - m2, a), (rf - d + m2, a)]) + _poly(
            [(rf - d + m2, top), (rf - m2, top), (rf - m2, height + 1), (rf - d + m2, height + 1)]
        )
        r_mid = rf - d / 2
        win_deg = math.degrees(22.0 / r_mid)
        wpitch = math.degrees(34.0 / r_mid)
        nw = max(1, int((90 - 10) // wpitch))
        wstart = (90 - (nw - 1) * wpitch - win_deg) / 2
        window = Manifold.revolve(lip_cut, 16, win_deg)
        for i in range(nw):
            chute = chute - window.rotate([0, 0, wstart + i * wpitch])
        if exit_len >= 40:  # one window and floor slot pair in the straight exit
            straight_lip = Manifold.extrude(lip_cut, exit_len - 20).translate([0, 0, -(exit_len - 10)])
            chute = chute - straight_lip.transform([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]])

        # Zip-tie holes near the top of the lead-in: one through the floor, one through each lip.
        y_tie = -(v["lead_in"] - 6)
        zc = (a + top) / 2
        tie_pts_print = {
            "floor": ((rf + t / 2, zc), (1.0, 0.0)),
            "lo_lip": ((rf - d / 2 + s / 2, a - d / 2 - s / 2), (1 / math.sqrt(2), -1 / math.sqrt(2))),
            "hi_lip": ((rf - d / 2 + s / 2, top + d / 2 + s / 2), (1 / math.sqrt(2), 1 / math.sqrt(2))),
        }
        for (pr, pz), _n in tie_pts_print.values():
            hole = Manifold.cube([8, 4, 8], center=True).translate([pr, y_tie, pz])
            chute = chute - hole

        geo = dict(t=t, d=d, wf=wf, rf=rf, a=a, top=top, zc=zc, height=height, y_tie=y_tie,
                   ties=tie_pts_print)
        return chute, geo

    @staticmethod
    def _to_installed(m: Manifold, zc: float) -> Manifold:
        # (x, y, z)_print -> (X = -x, Y = -(z - zc), Z = -y): enters from above, exits toward +X.
        return m.transform([[-1, 0, 0, 0], [0, 0, -1, zc], [0, -1, 0, 0]])

    # ------------------------------------------------------------------- ring
    def _ring(self, v, geo):
        r_in = v["ring_opening"] / 2
        t = geo["t"]
        # Installed frame: floor inner face sits at X = -rf; ring centre is in front of it.
        xc = -geo["rf"] + r_in + RING_BACK_GAP
        holes = []  # (X, Y) pairs of zip-tie holes either side of each wall
        for (pr, pz), (nr, nz) in geo["ties"].values():
            X, Y = -pr, -(pz - geo["zc"])
            nX, nY = -nr, -nz
            off = t / 2 + 2.6
            holes += [(X + nX * off, Y + nY * off), (X - nX * off, Y - nY * off)]
        dists = [math.hypot(x - xc, y) for x, y in holes]
        r_out = max(r_in + 14, max(dists) + 5)
        if min(dists) - TIE_HOLE_R < r_in + 1:
            r_in = min(dists) - TIE_HOLE_R - 1.5  # keep tie holes inside the band
        ring = Manifold.cylinder(RING_THICKNESS, r_out, circular_segments=SEG) - Manifold.cylinder(
            RING_THICKNESS + 2, r_in, circular_segments=SEG
        ).translate([0, 0, -1])
        ring = ring.translate([xc, 0, 0])
        for x, y in holes:
            ring = ring - Manifold.cylinder(RING_THICKNESS + 2, TIE_HOLE_R, circular_segments=16).translate(
                [x, y, -1]
            )
        r_cord = (r_in + r_out) / 2
        for ang in (45, -45, 110, -110):
            cx = xc + r_cord * math.cos(math.radians(ang))
            cy = r_cord * math.sin(math.radians(ang))
            ring = ring - Manifold.cylinder(RING_THICKNESS + 2, 2.5, circular_segments=20).translate([cx, cy, -1])
        return ring, r_in, r_out

    # ------------------------------------------------------------------- hook
    @staticmethod
    def _hook(v) -> Manifold:
        ri = v["rim_tube_diameter"] / 2 + 1.0
        w = 4.0
        ro = ri + w
        rm = ri + w / 2
        # Curl over the top of the tube: from the shank (180 deg) over the top to a tip at -35 deg.
        curl = _poly(_arc(0, 0, ro, 180, -35) + _arc(0, 0, ri, -35, 180))
        tip = CrossSection.circle(w / 2, 24).translate([rm * math.cos(math.radians(-35)),
                                                        rm * math.sin(math.radians(-35))])
        shank_len = 30.0
        shank = CrossSection.square([w, shank_len]).translate([-ro, -shank_len])
        eye = CrossSection.circle(5.0, 32).translate([-rm, -shank_len - 3]) - CrossSection.circle(
            2.2, 24
        ).translate([-rm, -shank_len - 3])
        return Manifold.extrude(curl + tip + shank + eye, 4.0)

    # ------------------------------------------------------------------ build
    def build(self, v: dict[str, float]) -> BuildResult:
        chute, geo = self._chute(v)
        ring, r_in, r_out = self._ring(v, geo)
        hook = self._hook(v)

        chute_inst = self._to_installed(chute, geo["zc"])
        ring_inst = ring.translate([0, 0, v["lead_in"]])
        assembled = [
            Part("Chute", chute_inst, CHUTE_COLOR),
            Part("Ring", ring_inst, RING_COLOR),
        ]
        # Preview only: cords up to the hooks (not exported).
        xc = -geo["rf"] + v["ring_opening"] / 2 + RING_BACK_GAP
        r_c = (r_in + r_out) / 2
        cord_len = 110.0
        b = hook.bounding_box()
        hook_up = hook.translate([-(b[0] + b[3]) / 2, -b[1], -2.0]).rotate([90, 0, 0])
        for ang in (45, -45, 110, -110):
            cx, cy = xc + r_c * math.cos(math.radians(ang)), r_c * math.sin(math.radians(ang))
            z0 = v["lead_in"] + RING_THICKNESS
            cord = Manifold.cylinder(cord_len, 1.5, circular_segments=8).translate([cx, cy, z0])
            assembled.append(Part("Cord", cord, "#888888"))
            hk = hook_up.rotate([0, 0, ang + 90]).translate([cx, cy, z0 + cord_len - 6])
            assembled.append(Part("Hook", hk, HOOK_COLOR))

        bed = v["bed_size"]
        print_parts, one_plate = pack_on_plate(
            [Part("Chute", chute, CHUTE_COLOR), Part("Ring", ring, RING_COLOR)]
            + [Part(f"Hook {i + 1}", hook, HOOK_COLOR) for i in range(4)],
            bed,
        )

        notes = []
        if not one_plate:
            notes.append("Not everything fits on one plate: parts that did not fit are placed to the "
                         "right of the plate. In Bambu Studio press A (Arrange) to move them to plate 2.")
        for p in print_parts[:2]:
            sx, sy, sz = p.size()
            if max(sx, sy) > bed or sz > bed:
                notes.append(f"Warning: the {p.name.lower()} is {sx:.0f} x {sy:.0f} x {sz:.0f} mm, "
                             f"larger than your {bed:.0f} mm bed. Reduce the bend radius or ring opening.")
        notes.append(
            "Bambu Studio: no supports needed. The chute stands on the edge of one lip, so keep the "
            "brim on (Auto) for grip. PETG or PLA."
        )
        notes.append(
            "Assembly: set the ring on top of the chute and fasten it with 3 small zip ties through "
            "the matching holes. Tie 4 cords (about 20-30 cm) from the ring's cord holes to the hook "
            "eyelets and hang the hooks on the rim so the ring sits just under the net."
        )
        return BuildResult(assembled, print_parts, notes)
