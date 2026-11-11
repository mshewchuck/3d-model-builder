"""Curved ball return in the style of store-bought hoop returns.

Parts (all print with no supports):
* Chute: a trough that bends (70 degrees by default, so the exit runs downhill), with a flat floor on the outside of
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

from manifold3d import CrossSection, JoinType, Manifold

from .base import BuildResult, Param, Part, Template, pack_on_plate

SEG = 96
CHUTE_COLOR = "#5b5f66"
RING_COLOR = "#f2c811"
HOOK_COLOR = "#2b2b2b"
RING_THICKNESS = 2.6
RING_BAND = 8.0  # slim hoop; tabs are added only where holes are
RING_BACK_GAP = 6.0  # ring opening starts this far in front of the floor
TIE_HOLE_R = 1.8
# Swivel (print-in-place): the inner ring (chute tied to it) and the outer ring (hangs from the
# cords) print nested together. A 45 degree ridge on the inner ring runs in a groove in the outer
# ring, so it prints without supports and comes off the plate already able to turn.
SWIVEL_GAP = 0.5  # clearance all round the ridge as printed
SWIVEL_LIFT = 1.0  # extra vertical room in the groove, so the ring can lift over the click bumps
RIDGE = 1.5  # ridge depth (its faces are 45 degrees)
RIDGE_Z0 = 1.0  # ridge starts this far above the plate
SWIVEL_H = RIDGE_Z0 + 2 * RIDGE + SWIVEL_LIFT / 2 + SWIVEL_GAP + 1.0  # ring height at the joint
INNER_RIM = 2.0
OUTER_RIM = 2.0
FLAT_T = 2.2  # thickness of the flat bands away from the joint
BUMP_P = 0.45  # how far the click bumps stand up
POSITIONS = 8
BUMP_ANGLES = (0, 135, 225)  # multiples of 360/8, spread for a stable three-point seat
CORD_ANGLES = (45, -45, 110, -110)


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
        Param("ball_diameter", "Ball diameter", 80, 40, 130,
              help="Default fits an 80 mm mini airless ball. Measure yours."),
        Param("ring_opening", "Ring opening", 110, 60, 200,
              help="Inside diameter of the catch ring. A bit bigger than the bottom of your net."),
        Param("bend_radius", "Bend radius", 100, 50, 200,
              help="Radius of the chute's floor through the turn. Bigger turns more smoothly but is bigger to print."),
        Param("bend_angle", "Bend angle", 70, 30, 90, unit="deg",
              help="How far the chute turns from straight down. 70 means the exit slopes 20 degrees downhill toward you."),
        Param("lead_in", "Straight section at top", 25, 10, 100),
        Param("exit_length", "Spout length", 60, 0, 150,
              help="Straight run after the turn. The end of it is rounded off into the spout."),
        Param("wall", "Wall thickness", 2.0, 1.6, 5),
        Param("swivel", "Swivel ring (1 = on, 0 = off)", 1, 0, 1, unit="",
              help="On: the chute sits in a turning inner ring that clicks into 8 directions. "
                   "Off: one fixed ring (lighter); turn it by sliding the hooks around the rim."),
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

        floor = _poly([(rf, a), (rf + t, a), (rf + t, top + s), (rf, top + s)])
        lo_lip = _poly([(rf, a), (rf - d, a - d), (rf - d + s, a - d - s), (rf + s, a - s)])
        hi_lip = _poly([(rf, top), (rf + s, top + s), (rf - d + s, top + d + s), (rf - d, top + d)])
        # Lower corner is chamfered at 45 degrees so nothing overhangs flat while printing.
        corners = _poly([(rf, a), (rf + s, a - s), (rf + t, a - s + (t - s)), (rf + t, a)]) + _poly(
            [(rf, top), (rf + t, top), (rf + t, top + s), (rf + s, top + s)]
        )
        profile = floor + lo_lip + hi_lip + corners

        angle = v["bend_angle"]
        bend = Manifold.revolve(profile, SEG, angle)
        lead = Manifold.extrude(profile, v["lead_in"] + 0.5).translate([0, 0, -0.5]).transform(
            [[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0]]
        )  # runs along -Y from the start of the bend
        chute = bend + lead
        exit_len = v["exit_length"]
        if exit_len > 0:
            ext = Manifold.extrude(profile, exit_len + 0.5)  # 0.5 mm overlap fuses it to the bend
            # Rounded spout: in this local frame the spout end is at w = 0. The lips curve down to
            # the floor along a quarter circle. The cut surface is vertical while printing, so it
            # adds no overhang.
            rc = min(d + t, exit_len)
            keep = Manifold.cube([rf + t + 10, height + 4, exit_len + 1]).translate([0, -2, rc])
            keep = keep + Manifold.cylinder(height + 4, rc, circular_segments=SEG).rotate(
                [-90, 0, 0]).translate([rf + t, -2, rc])
            ext = ext ^ keep
            chute = chute + self._exit(ext, exit_len, angle)

        # Floor slots across the path (8 mm wide, so the ball rolls straight over them).
        m = 5.0
        floor_cut = _poly([(rf - 1, a + m), (rf + t + 1, a + m), (rf + t + 1, top - m), (rf - 1, top - m)])
        slot_deg = math.degrees(10.0 / rf)
        pitch_deg = math.degrees(16.0 / rf)
        n = max(0, int((angle - 2 * pitch_deg) // pitch_deg) + 1)
        start = (angle - (n - 1) * pitch_deg - slot_deg) / 2
        slot = Manifold.revolve(floor_cut, 8, slot_deg)
        for i in range(n):
            chute = chute - slot.rotate([0, 0, start + i * pitch_deg])

        # Slots in the lips (the open-frame look). 10 mm wide, so the print only bridges 10 mm.
        m2 = 5.0
        lip_cut = _poly([(rf - d + m2, -1), (rf - m2, -1), (rf - m2, a), (rf - d + m2, a)]) + _poly(
            [(rf - d + m2, top), (rf - m2, top), (rf - m2, height + 1), (rf - d + m2, height + 1)]
        )
        r_mid = rf - d / 2
        win_deg = math.degrees(10.0 / r_mid)
        wpitch = math.degrees(16.0 / r_mid)
        nw = max(1, int((angle - 2 * wpitch) // wpitch) + 1)
        wstart = (angle - (nw - 1) * wpitch - win_deg) / 2
        window = Manifold.revolve(lip_cut, 8, win_deg)
        for i in range(nw):
            chute = chute - window.rotate([0, 0, wstart + i * wpitch])
        # Matching slots along the straight exit. Lip slots stop where the rounded spout begins.
        rounded_from = exit_len - min(d + t, exit_len)
        pos = 6.0
        while pos + 10 <= exit_len - 8:
            cut = floor_cut + lip_cut if pos + 10 <= rounded_from - 3 else floor_cut
            piece = Manifold.extrude(cut, 10.0).translate([0, 0, -(pos + 10)])
            chute = chute - self._exit(piece, 0, angle)
            pos += 16.0

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
    def _exit(m: Manifold, length: float, angle: float) -> Manifold:
        """Place an extrusion (local w in [0, length], or already shifted negative) on the tangent
        leaving the end of the bend, which sits at `angle` degrees around Z."""
        if length:
            m = m.translate([0, 0, -length])
        m = m.transform([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]])  # tangent exit at 90 deg
        return m.rotate([0, 0, angle - 90])

    @staticmethod
    def _to_installed(m: Manifold, zc: float) -> Manifold:
        # (x, y, z)_print -> (X = -x, Y = -(z - zc), Z = -y): enters from above, exits toward +X.
        return m.transform([[-1, 0, 0, 0], [0, 0, -1, zc], [0, -1, 0, 0]])

    # ------------------------------------------------------------------- ring
    def _ring(self, v, geo):
        r_in = v["ring_opening"] / 2
        r_out = r_in + RING_BAND
        r_mid = (r_in + r_out) / 2
        t = geo["t"]
        # Installed frame: floor inner face sits at X = -rf; ring centre is in front of it.
        xc = -geo["rf"] + r_in + RING_BACK_GAP
        band = CrossSection.circle(r_out, SEG) - CrossSection.circle(r_in, SEG)
        tie_holes = []
        for (pr, pz), (nr, nz) in geo["ties"].values():
            X, Y = -pr - xc, -(pz - geo["zc"])  # relative to ring centre
            nX, nY = -nr, -nz
            off = t / 2 + 2.6
            pair = [(X + nX * off, Y + nY * off), (X - nX * off, Y - nY * off)]
            tie_holes += pair
            ang = math.atan2(Y, X)
            anchor = (r_mid * math.cos(ang), r_mid * math.sin(ang))
            band = band + CrossSection.batch_hull(
                [CrossSection.circle(TIE_HOLE_R + 2.6, 24).translate(list(q)) for q in pair + [anchor]]
            )
        cord_pts = []
        for ang in (45, -45, 110, -110):
            q = (r_mid * math.cos(math.radians(ang)), r_mid * math.sin(math.radians(ang)))
            cord_pts.append(q)
            band = band + CrossSection.circle(5.5, 32).translate(list(q))
        for q in tie_holes:
            band = band - CrossSection.circle(TIE_HOLE_R, 16).translate(list(q))
        for q in cord_pts:
            band = band - CrossSection.circle(2.5, 20).translate(list(q))
        ring = Manifold.extrude(band, RING_THICKNESS).translate([xc, 0, 0])
        return ring, r_in, r_out

    # ----------------------------------------------------------------- swivel
    def _swivel(self, v, geo, chute_inst):
        """Nested print-in-place swivel ring, in the installed frame (bottom at the chute top)."""
        r_in = v["ring_opening"] / 2
        t = geo["t"]
        z0 = v["lead_in"]
        xc = -geo["rf"] + r_in + RING_BACK_GAP

        ties = []
        for (pr, pz), (nr, nz) in geo["ties"].values():
            X, Y = -pr - xc, -(pz - geo["zc"])
            nX, nY = -nr, -nz
            off = t / 2 + 2.6
            ties.append([(X + nX * off, Y + nY * off), (X - nX * off, Y - nY * off)])
        tie_r = max(math.hypot(*q) for pair in ties for q in pair)

        # Inner ring: flat band + tie tabs, with a taller rim carrying the ridge on its outside.
        ri = max(r_in + 8, tie_r + TIE_HOLE_R + 2.6 + INNER_RIM)  # outside of the inner rim
        flat = CrossSection.circle(ri, SEG) - CrossSection.circle(max(r_in, ri - 6), SEG)
        for pair in ties:
            ang = math.atan2(sum(q[1] for q in pair), sum(q[0] for q in pair))
            anchor = ((ri - 3) * math.cos(ang), (ri - 3) * math.sin(ang))
            flat = flat + CrossSection.batch_hull(
                [CrossSection.circle(TIE_HOLE_R + 2.6, 24).translate(list(q)) for q in pair + [anchor]]
            )
        flat = flat ^ CrossSection.circle(ri, SEG)
        for pair in ties:
            for q in pair:
                flat = flat - CrossSection.circle(TIE_HOLE_R, 16).translate(list(q))
        inner = Manifold.extrude(flat, FLAT_T)
        rim_prof = _poly([(ri - INNER_RIM, 0), (ri, 0), (ri, SWIVEL_H), (ri - INNER_RIM, SWIVEL_H)])
        z1 = RIDGE_Z0 + SWIVEL_LIFT / 2 + SWIVEL_GAP  # ridge sits mid-groove as printed
        ridge = _poly([(ri - 0.5, z1), (ri + RIDGE, z1 + RIDGE), (ri - 0.5, z1 + 2 * RIDGE + 0.5)])
        inner = inner + Manifold.revolve(rim_prof + ridge, SEG)

        # Outer ring: rim with a matching groove (ridge grown by the gap, stretched by the lift).
        ro_in = ri + SWIVEL_GAP
        ro_out = ri + RIDGE + SWIVEL_GAP + OUTER_RIM
        groove = CrossSection.batch_hull([
            ridge.offset(SWIVEL_GAP, JoinType.Miter).translate([0, -SWIVEL_LIFT / 2]),
            ridge.offset(SWIVEL_GAP, JoinType.Miter).translate([0, SWIVEL_LIFT / 2]),
        ])
        outer_prof = _poly([(ro_in, 0), (ro_out, 0), (ro_out, SWIVEL_H), (ro_in, SWIVEL_H)]) - groove
        outer = Manifold.revolve(outer_prof, SEG)

        # Clicks: bumps on the groove's lower face, dimples in the ridge's lower face.
        n = (1 / math.sqrt(2), -1 / math.sqrt(2))  # outward-down normal of the ridge's lower face
        mid = (ri + RIDGE / 2, z1 + RIDGE / 2)
        face_gap = SWIVEL_GAP + (SWIVEL_LIFT / 2) / math.sqrt(2)
        groove_mid = (mid[0] + n[0] * face_gap, mid[1] + n[1] * face_gap)
        br = 1.0
        bump_c = (groove_mid[0] + n[0] * (br - BUMP_P), groove_mid[1] + n[1] * (br - BUMP_P))
        dimple_c = (mid[0] + n[0] * (1.3 - BUMP_P - 0.15), mid[1] + n[1] * (1.3 - BUMP_P - 0.15))
        for ang in BUMP_ANGLES:
            a = math.radians(ang)
            outer = outer + Manifold.sphere(br, 16).translate(
                [bump_c[0] * math.cos(a), bump_c[0] * math.sin(a), bump_c[1]])
        # As the ring settles it slides down the 45 degree face, so the dimple is stretched up the
        # slope to keep catching the bump.
        u = (1 / math.sqrt(2), 1 / math.sqrt(2))
        d2 = (dimple_c[0] + u[0] * 1.1, dimple_c[1] + u[1] * 1.1)
        for i in range(POSITIONS):
            a = math.radians(i * 360 / POSITIONS)
            c, sn = math.cos(a), math.sin(a)
            dimple = Manifold.batch_hull([
                Manifold.sphere(1.3, 16).translate([dimple_c[0] * c, dimple_c[0] * sn, dimple_c[1]]),
                Manifold.sphere(1.3, 16).translate([d2[0] * c, d2[0] * sn, d2[1]]),
            ])
            inner = inner - dimple

        # Cord bosses on the outside of the outer ring.
        r_cord = ro_out + 3.0
        bosses, holes, cords = CrossSection(), CrossSection(), []
        for ang in CORD_ANGLES:
            q = (r_cord * math.cos(math.radians(ang)), r_cord * math.sin(math.radians(ang)))
            cords.append(q)
            bosses = bosses + CrossSection.circle(5.5, 32).translate(list(q))
            holes = holes + CrossSection.circle(2.5, 20).translate(list(q))
        outer = outer + Manifold.extrude(bosses - CrossSection.circle(ro_out - 0.5, SEG), FLAT_T)
        outer = outer - Manifold.extrude(holes, SWIVEL_H + 2).translate([0, 0, -1])

        inner = inner.translate([xc, 0, z0])
        outer = outer.translate([xc, 0, z0])
        cord_pts = [(xc + x, y) for x, y in cords]
        return inner, outer, cord_pts, z0 + FLAT_T

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
        hook = self._hook(v)
        chute_inst = self._to_installed(chute, geo["zc"])
        assembled = [Part("Chute", chute_inst, CHUTE_COLOR)]
        if v["swivel"] >= 0.5:
            inner_ring, outer_ring, cord_pts, cord_z = self._swivel(v, geo, chute_inst)
            rings = [Part("Swivel ring (print-in-place)", inner_ring + outer_ring, RING_COLOR)]
            assembled += [Part("Inner ring (turns)", inner_ring, "#f7dc6f"),
                          Part("Outer ring (hangs)", outer_ring, RING_COLOR)]
        else:
            ring, r_in, r_out = self._ring(v, geo)
            ring_inst = ring.translate([0, 0, v["lead_in"]])
            rings = [Part("Ring", ring_inst, RING_COLOR)]
            xc = -geo["rf"] + v["ring_opening"] / 2 + RING_BACK_GAP
            r_c = (r_in + r_out) / 2
            cord_pts = [(xc + r_c * math.cos(math.radians(a)), r_c * math.sin(math.radians(a)))
                        for a in CORD_ANGLES]
            cord_z = v["lead_in"] + RING_THICKNESS
        if v["swivel"] < 0.5:
            assembled += rings
        # Preview only: cords up to the hooks (not exported).
        cord_len = 110.0
        b = hook.bounding_box()
        hook_up = hook.translate([-(b[0] + b[3]) / 2, -b[1], -2.0]).rotate([90, 0, 0])
        for (cx, cy), ang in zip(cord_pts, CORD_ANGLES):
            z0 = cord_z
            cord = Manifold.cylinder(cord_len, 1.5, circular_segments=8).translate([cx, cy, z0])
            assembled.append(Part("Cord", cord, "#888888"))
            hk = hook_up.rotate([0, 0, ang + 90]).translate([cx, cy, z0 + cord_len - 6])
            assembled.append(Part("Hook", hk, HOOK_COLOR))

        bed = v["bed_size"]
        others = list(rings) + [
            Part(f"Hook {i + 1}", hook, HOOK_COLOR) for i in range(4)
        ]
        # Spin the chute flat on the plate until everything packs onto one plate.
        for spin in range(0, 180, 10):
            print_parts, one_plate = pack_on_plate(
                [Part("Chute", chute.rotate([0, 0, spin]), CHUTE_COLOR)] + others, bed
            )
            if one_plate:
                break

        notes = []
        if not one_plate:
            notes.append("Not everything fits on one plate: parts that did not fit are placed to the "
                         "right of the plate. In Bambu Studio press A (Arrange) to move them to plate 2.")
        for p in print_parts[: 1 + len(rings)]:
            sx, sy, sz = p.size()
            if max(sx, sy) > bed or sz > bed:
                notes.append(f"Warning: the {p.name.lower()} is {sx:.0f} x {sy:.0f} x {sz:.0f} mm, "
                             f"larger than your {bed:.0f} mm bed. Reduce the bend radius or ring opening.")
        notes.append(
            "Bambu Studio: supports OFF. The chute prints lying on its side (the curve flat on the "
            "plate): walls are vertical or 45 degrees and slots bridge 10 mm at most. Its lower lip "
            "edge is all that touches the plate, so set Brim to Outer only (about 5 mm). PETG or PLA."
        )
        tied_to = "inner ring" if v["swivel"] >= 0.5 else "ring"
        notes.append(
            f"Chute to ring: the chute's top end sits flat against the underside of the {tied_to}. "
            "3 small zip ties (2.5-3.6 mm wide) lock it on: one at the back wall and one at each side "
            "lip. Each tie goes down through a ring hole, through the slot in the chute wall, and back "
            "up through the ring hole on the other side of the wall. Pull it tight and trim it."
        )
        if v["swivel"] >= 0.5:
            notes.append(
                "Swivel ring: prints as ONE part with the inner ring nested inside the outer ring "
                "(0.5 mm gap). After printing, twist it firmly once to break it free. To aim the "
                "chute, lift it slightly, turn it, and let it settle into the next click. There are "
                "8 positions, 45 degrees apart. Print it at 0.2 mm layers or finer. Don't scale it in "
                "the slicer, because that changes the gap."
            )
        notes.append(
            "Hanging: tie 4 cords (about 20-30 cm) from the cord holes to the hook eyelets and hang "
            "the hooks on the rim so the ring sits just under the net."
        )
        return BuildResult(assembled, print_parts, notes)
