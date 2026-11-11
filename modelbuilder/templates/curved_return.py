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

from .base import BuildResult, Param, Part, Template, pack_plates

SEG = 96
CHUTE_COLOR = "#5b5f66"
RING_COLOR = "#f2c811"
HOOK_COLOR = "#2b2b2b"
HANGER_COLOR = "#2b2b2b"
RING_THICKNESS = 2.6
RING_BAND = 8.0  # slim hoop; tabs are added only where holes are
RING_BACK_GAP = 6.0  # ring opening starts this far in front of the floor
TIE_HOLE_R = 1.8
SIDE_CLEARANCE = 5.0  # room each side of the ball between the side panels
EAR = 6.0  # how far the joining ears stick out behind the floor
EAR_W = 12.0  # ear width along the chute
EAR_HOLE_R = 1.7  # M3 screw or a small zip tie
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
# Backboard hanger: caps the block where the rim meets the backboard.
CAP_FIT = 0.4  # clearance around the block
CAP_T = 2.4  # cap wall thickness
FINGER = 6.0  # size of the two front fingers that stop the cap sliding off the block
LEG_W = 10.0  # leg / spine width
LEG_T = 4.0  # leg thickness (lies flat against the backboard)
BRACKET_T = 4.0
BRACKET_W = 30.0
TAB_LEN = 16.0  # tab on the ring that the bracket screws to
SCREW_R = 1.7  # M3


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
        Param("mount", "Mount (1 = backboard bracket, 0 = rim hooks)", 1, 0, 1, unit="",
              help="1: hang it from the block where the rim joins the backboard. "
                   "0: hang the ring from the rim on 4 cords with printed hooks."),
        Param("block_width", "Rim block width", 57.2, 20, 150,
              help="Side to side, along the backboard (2.25 in = 57.2 mm)."),
        Param("block_depth", "Rim block depth", 25.4, 5, 80,
              help="How far it sticks out from the backboard (1 in = 25.4 mm)."),
        Param("block_height", "Rim block height", 12.7, 5, 80,
              help="Top to bottom (0.5 in = 12.7 mm)."),
        Param("board_to_center", "Backboard to rim centre", 110, 60, 300,
              help="Straight out from the backboard to the middle of the rim. The ring centres here."),
        Param("drop", "Block to ring drop", 170, 60, 400,
              help="From the bottom of the rim block down to the top of the ring. Make it longer than "
                   "the net so the ball falls out of the net first."),
        Param("rim_tube_diameter", "Rim tube diameter", 12, 4, 30,
              help="Thickness of the rim's metal tube. Sets the size of the hooks."),
        Param("bed_size", "Printer bed size", 256, 150, 400,
              help="256 for Bambu X1/P1/P2, 180 for the A1 mini."),
    ]

    # ------------------------------------------------------------------ chute
    def _chute(self, v):
        """Build one chute half (print-ready) and the full chute (for the installed view).

        Cross-section (print frame, r = distance from the bend axis, z = up): a U channel with
        a flat floor on the outside of the bend and two flat side panels. It is split down the
        middle of the floor (z = zc) into two identical halves. Each half prints lying on its
        side panel: a flat plate (big footprint, windows need no bridging) with the half floor
        rising from it as a short vertical wall. Ears with holes along the back join the halves.
        """
        t = v["wall"]
        ball = v["ball_diameter"]
        w_in = ball + 2 * SIDE_CLEARANCE  # inside width between the side panels
        depth = 0.6 * ball  # side panels reach this far in from the floor (past the ball centre)
        rf = v["bend_radius"]  # floor inner face radius
        zc = t + w_in / 2  # the split plane (centre of the floor)
        angle = v["bend_angle"]
        lead_len = v["lead_in"]
        exit_len = v["exit_length"]

        profile = _poly([(rf - depth, 0), (rf + t, 0), (rf + t, zc), (rf, zc), (rf, t), (rf - depth, t)])

        def along_lead(m):  # extrusion local w in [0, L] -> runs along -Y from the bend start
            return m.transform([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0]])

        half = Manifold.revolve(profile, SEG, angle)
        half = half + along_lead(Manifold.extrude(profile, lead_len + 0.5).translate([0, 0, -0.5]))
        rc = min(depth + t, exit_len) if exit_len > 0 else 0
        if exit_len > 0:
            ext = Manifold.extrude(profile, exit_len + 0.5)  # 0.5 mm overlap fuses it to the bend
            # Rounded spout: the side panel curves down to the floor along a quarter circle.
            # The cut is vertical while printing, so it adds no overhang.
            keep = Manifold.cube([rf + t + 10, zc + 4, exit_len + 1]).translate([0, -2, rc])
            keep = keep + Manifold.cylinder(zc + 4, rc, circular_segments=SEG).rotate(
                [-90, 0, 0]).translate([rf + t, -2, rc])
            half = half + self._exit(ext ^ keep, exit_len, angle)

        # Windows in the side panel (flat on the plate, so any size prints cleanly).
        mw = 6.0
        win = _poly([(rf - depth + mw, -1), (rf - mw, -1), (rf - mw, t + 1), (rf - depth + mw, t + 1)])
        r_mid = rf - depth / 2
        win_deg, rib_deg = math.degrees(24.0 / r_mid), math.degrees(8.0 / r_mid)
        pitch = win_deg + rib_deg
        nw = max(0, int((angle - rib_deg) // pitch))
        w0 = (angle - nw * pitch + rib_deg) / 2
        window = Manifold.revolve(win, 8, win_deg)
        for i in range(nw):
            half = half - window.rotate([0, 0, w0 + i * pitch])

        # Floor slots across the path. As printed the floor is a vertical wall, so each slot's
        # top is a 10 mm bridge. A 4 mm strip is left along the seam.
        floor_cut = _poly([(rf - 1, t + 4), (rf + t + 1, t + 4), (rf + t + 1, zc - 4), (rf - 1, zc - 4)])
        slot_deg, fpitch = math.degrees(10.0 / rf), math.degrees(16.0 / rf)
        n = max(0, int((angle - 2 * fpitch) // fpitch) + 1)
        start = (angle - (n - 1) * fpitch - slot_deg) / 2
        slot = Manifold.revolve(floor_cut, 8, slot_deg)
        for i in range(n):
            half = half - slot.rotate([0, 0, start + i * fpitch])
        rounded_from = exit_len - rc
        pos = 6.0
        while exit_len > 0 and pos + 10 <= exit_len - 8:
            cut = floor_cut + win if pos + 10 <= rounded_from - 3 else floor_cut
            half = half - self._exit(Manifold.extrude(cut, 10.0).translate([0, 0, -(pos + 10)]), 0, angle)
            pos += 16.0

        # Ears along the back: each half has a matching ear; bolt or zip-tie them together.
        ear_prof = _poly([(rf + t - 0.3, zc - 12), (rf + t + EAR, zc - 12 + EAR + 0.3), (rf + t + EAR, zc),
                          (rf + t - 0.3, zc)])  # 45 degree underside, so it prints unsupported
        r_hole = rf + t + EAR / 2 + 0.5
        ear_deg = math.degrees(EAR_W / (rf + t))
        for frac in (0.2, 0.5, 0.8):
            a0 = angle * frac - ear_deg / 2
            ear = Manifold.revolve(ear_prof, 8, ear_deg).rotate([0, 0, a0])
            ac = math.radians(angle * frac)
            hole = Manifold.cylinder(20, EAR_HOLE_R, circular_segments=16).translate(
                [r_hole * math.cos(ac), r_hole * math.sin(ac), zc - 15])
            half = half + ear - hole

        def straight_ear(place, w_c):
            e = Manifold.extrude(ear_prof, EAR_W).translate([0, 0, -EAR_W / 2])
            h = Manifold.cylinder(20, EAR_HOLE_R, circular_segments=16).rotate([-90, 0, 0])
            h = h.translate([r_hole, zc - 15, 0])
            return place((e - h).translate([0, 0, w_c]))

        half = half + straight_ear(along_lead, lead_len * 0.4)
        if exit_len - rc >= EAR_W + 4:
            half = half + self._exit(straight_ear(lambda m: m, -(exit_len - rc) / 2), 0, angle)

        # Ring tie slots near the top of the lead-in: one through the floor and one through the
        # side panel on each half (4 ties in all, symmetric).
        y_tie = -(lead_len - 6)
        floor_tie_z = zc - 10
        half = half - Manifold.cube([8, 4, 6], center=True).translate([rf + t / 2, y_tie, floor_tie_z])
        half = half - Manifold.cube([8, 4, t + 2], center=True).translate([rf - depth / 2, y_tie, t / 2])

        full = half + half.mirror([0, 0, 1]).translate([0, 0, 2 * zc])
        ties = {
            "floor_a": ((rf + t / 2, floor_tie_z), (1.0, 0.0)),
            "floor_b": ((rf + t / 2, 2 * zc - floor_tie_z), (1.0, 0.0)),
            "side_a": ((rf - depth / 2, t / 2), (0.0, -1.0)),
            "side_b": ((rf - depth / 2, 2 * zc - t / 2), (0.0, 1.0)),
        }
        geo = dict(t=t, rf=rf, zc=zc, w_in=w_in, depth=depth, ties=ties, y_tie=y_tie)
        return half, full, geo

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

    # ----------------------------------------------------------------- hanger
    def _ring_tab(self, xc, r_back, z0, height):
        """Solid tab on the back of the hanging ring with 2 screw holes (prints from the plate)."""
        x0 = xc - r_back - TAB_LEN + 1.5  # only 1.5 mm onto the outer rim, clear of the inner ring
        tab = Manifold.cube([TAB_LEN, BRACKET_W - 4, height]).translate([x0, -(BRACKET_W - 4) / 2, z0])
        # Screws spaced front-to-back as well as side-to-side, so the ring can't tip forward.
        holes = [(x0 + 4.0, -7.0), (x0 + TAB_LEN - 5.0, 7.0)]
        for x, y in holes:
            tab = tab - Manifold.cylinder(height + 2, SCREW_R, circular_segments=16).translate([x, y, z0 - 1])
        return tab, holes

    def _hanger(self, v, x_board, z_bracket, holes):
        """One-piece hanger in the installed frame. Prints lying on its backboard side."""
        bw, bd, bh = v["block_width"], v["block_depth"], v["block_height"]
        f, t = CAP_FIT, CAP_T
        zb = z_bracket + BRACKET_T + v["drop"]  # bottom of the rim block
        top = zb + bh
        xo = x_board
        yo = bw / 2 + f  # inside face of the end plates

        def box(x0, x1, y0, y1, z0, z1):
            return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

        cap = box(xo, xo + bd + f + t, -(yo + t), yo + t, top + f, top + f + t)  # sits on the block
        for sgn in (1, -1):
            y0, y1 = sorted((sgn * yo, sgn * (yo + t)))
            cap = cap + box(xo, xo + bd + f + t, y0, y1, zb + 0.4 * bh, top + f + t)  # end plates
            fy0, fy1 = sorted((sgn * (bw / 2 - FINGER), sgn * (yo + t)))
            cap = cap + box(xo + bd + f, xo + bd + f + t, fy0, fy1, top - FINGER, top + f + t)

        # Legs down past the block ends, joining into one spine (a flat profile on the board).
        z_join = zb - 30
        z_low = z_bracket + BRACKET_T + 30
        legs = CrossSection()
        for sgn in (1, -1):
            yl = sgn * (yo + t / 2 + LEG_W / 2 - t / 2)
            legs = legs + CrossSection.batch_hull([
                CrossSection.square([LEG_W, 1], center=True).translate([yl, zb + 0.4 * bh + 0.5]),
                CrossSection.square([LEG_W, 1], center=True).translate([yl, zb - 6]),
            ])
            legs = legs + CrossSection.batch_hull([
                CrossSection.circle(LEG_W / 2, 24).translate([yl, zb - 6]),
                CrossSection.circle(LEG_W / 2, 24).translate([0, z_join]),
            ])
        legs = legs + CrossSection.square([LEG_W, z_join - z_low]).translate([-LEG_W / 2, z_low])
        legs = legs + CrossSection.batch_hull([  # flare into the bracket
            CrossSection.square([LEG_W, 1]).translate([-LEG_W / 2, z_low]),
            CrossSection.square([BRACKET_W, 1]).translate([-BRACKET_W / 2, z_bracket]),
        ])
        # Profile (y, z) extruded along +X from the board: map local (u, w, e) -> (x = e, y = u, z = w).
        spine = Manifold.extrude(legs, LEG_T).transform([[0, 0, 1, xo], [1, 0, 0, 0], [0, 1, 0, 0]])

        # Shelf straight out from the board; the ring's tab screws up under it.
        x_end = max(x for x, _ in holes) + 6
        bracket = box(xo, x_end, -BRACKET_W / 2, BRACKET_W / 2, z_bracket, z_bracket + BRACKET_T)
        lg = min(x_end - xo - 8, 30.0)  # 45 degree gussets above the shelf
        for y in (-BRACKET_W / 2, BRACKET_W / 2 - 3):
            g = _poly([(0, 0), (lg, 0), (0, lg)])
            gus = Manifold.extrude(g, 3).transform([[1, 0, 0, xo], [0, 0, 1, y], [0, 1, 0, z_bracket + BRACKET_T]])
            bracket = bracket + gus
        for x, y in holes:
            bracket = bracket - Manifold.cylinder(BRACKET_T + 2, SCREW_R, circular_segments=16).translate(
                [x, y, z_bracket - 1])
        return cap + spine + bracket

    # ------------------------------------------------------------------ build
    def build(self, v: dict[str, float]) -> BuildResult:
        half, chute, geo = self._chute(v)
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
        hanger = None
        if v["mount"] >= 0.5:
            xc = -geo["rf"] + v["ring_opening"] / 2 + RING_BACK_GAP
            hang = outer_ring if v["swivel"] >= 0.5 else ring_inst
            hb = hang.bounding_box()
            r_back = xc - hb[0]
            tab, holes = self._ring_tab(xc, r_back, hb[2], hb[5] - hb[2])
            hang = hang + tab
            if v["swivel"] >= 0.5:
                outer_ring = hang
                rings = [Part("Swivel ring (print-in-place)", inner_ring + outer_ring, RING_COLOR)]
                assembled = [p for p in assembled if not p.name.startswith("Outer")]
                assembled.append(Part("Outer ring (hangs)", outer_ring, RING_COLOR))
            else:
                ring_inst = hang
                rings = [Part("Ring", ring_inst, RING_COLOR)]
            x_board = xc - v["board_to_center"]
            if x_board > hb[0] - 5:
                raise ValueError("Backboard to rim centre is too short: the ring would hit the board.")
            hanger = self._hanger(v, x_board, hb[5], holes)
            assembled.append(Part("Hanger", hanger, HANGER_COLOR))
            # Preview only: the rim block and a slice of backboard.
            zb = hb[5] + BRACKET_T + v["drop"]
            blk = Manifold.cube([v["block_depth"], v["block_width"], v["block_height"]]).translate(
                [x_board, -v["block_width"] / 2, zb])
            board = Manifold.cube([2, 200, 320]).translate([x_board - 2, -100, hb[2] - 120])
            assembled += [Part("Rim block", blk, "#ff5a1f"), Part("Backboard", board, "#e8e8e8")]
        if v["swivel"] < 0.5:
            assembled += rings
        # Preview only: cords up to the hooks (not exported).
        cord_len = 110.0
        b = hook.bounding_box()
        hook_up = hook.translate([-(b[0] + b[3]) / 2, -b[1], -2.0]).rotate([90, 0, 0])
        for (cx, cy), ang in zip(cord_pts if v["mount"] < 0.5 else [], CORD_ANGLES):
            z0 = cord_z
            cord = Manifold.cylinder(cord_len, 1.5, circular_segments=8).translate([cx, cy, z0])
            assembled.append(Part("Cord", cord, "#888888"))
            hk = hook_up.rotate([0, 0, ang + 90]).translate([cx, cy, z0 + cord_len - 6])
            assembled.append(Part("Hook", hk, HOOK_COLOR))

        bed = v["bed_size"]
        if hanger is not None:
            others = list(rings) + [Part("Hanger", hanger.rotate([0, -90, 0]), HANGER_COLOR)]
        else:
            others = list(rings) + [Part(f"Hook {i + 1}", hook, HOOK_COLOR) for i in range(4)]
        # Spin the halves on the plate to find the packing that uses the fewest plates.
        best = None
        for spin in range(0, 180, 15):
            h = half.rotate([0, 0, spin])
            result = pack_plates(
                [Part("Chute half A", h, CHUTE_COLOR), Part("Chute half B", h, CHUTE_COLOR)] + others, bed
            )
            if best is None or result[1] < best[1]:
                best = result
            if result[1] == 1:
                break
        print_parts, n_plates = best

        notes = []
        if n_plates > 1:
            notes.append(f"Needs {n_plates} plates on a {bed:.0f} mm bed. The file lays them out side "
                         "by side. In Bambu Studio add a plate and press A (Arrange), and it will "
                         "split them.")
        for p in print_parts[: 2 + len(rings)]:
            sx, sy, sz = p.size()
            if max(sx, sy) > bed or sz > bed:
                notes.append(f"Warning: the {p.name.lower()} is {sx:.0f} x {sy:.0f} x {sz:.0f} mm, "
                             f"larger than your {bed:.0f} mm bed. Reduce the bend radius or ring opening.")
        notes.append(
            "Bambu Studio: supports OFF. The chute is two identical halves. Each prints lying flat "
            "on its side panel, with the half floor standing up as a short wall. Floor slots bridge "
            "10 mm at most. PETG or PLA."
        )
        tied_to = "inner ring" if v["swivel"] >= 0.5 else "ring"
        notes.append(
            "Joining the halves: line up the two halves floor to floor. The 5 ears along the back "
            "pair up. Put an M3 x 20 mm screw and nut, or a small zip tie, through each pair."
        )
        notes.append(
            f"Chute to ring: the chute's top end sits flat against the underside of the {tied_to}. "
            "4 small zip ties (2.5-3.6 mm wide) lock it on: two through the back wall and one through "
            "each side panel. Each tie goes down through a ring hole, through the slot in the chute "
            "wall, and back up through the ring hole on the other side. Pull it tight and trim it."
        )
        if v["swivel"] >= 0.5:
            notes.append(
                "Swivel ring: prints as ONE part with the inner ring nested inside the outer ring "
                "(0.5 mm gap). After printing, twist it firmly once to break it free. To aim the "
                "chute, lift it slightly, turn it, and let it settle into the next click. There are "
                "8 positions, 45 degrees apart. Print it at 0.2 mm layers or finer. Don't scale it in "
                "the slicer, because that changes the gap."
            )
        if hanger is not None:
            notes.append(
                "Hanging: press the hanger's cap down over the block where the rim joins the "
                "backboard. Its legs run down the board around the block ends. Screw the ring's back "
                "tab up under the hanger shelf with 2 M3 x 12 mm screws and nuts. The hanger prints "
                "lying on its backboard side. Measure the block and the board-to-rim-centre "
                "distance, because the cap is a snug 0.4 mm fit."
            )
        else:
            notes.append(
                "Hanging: tie 4 cords (about 20-30 cm) from the cord holes to the hook eyelets and "
                "hang the hooks on the rim so the ring sits just under the net."
            )
        return BuildResult(assembled, print_parts, notes)
