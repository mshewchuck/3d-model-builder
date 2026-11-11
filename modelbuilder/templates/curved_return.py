"""Curved ball return in the style of store-bought hoop returns.

Parts (all print with no supports):
* Chute: a U channel that bends (65 degrees by default, so the exit runs downhill) with a
  slotted floor, flat side panels with windows, and a rounded spout. It is exported as one part
  lying on a side panel; cut it in half in the slicer (a flat cut at half its height) and each
  half prints flat on its side panel. A slim glue bead and filament pins rejoin the halves.
* Hanger: caps the block where the rim joins the backboard, runs down the board as a spine,
  and ends in a short block (with support triangles) that the back of the chute screws to.
  Prints lying on its backboard side.

Frames: the chute is built lying on the bed (the "print frame") with the bend centred on the Z
axis. It enters along -Y and leaves along -X. `_to_installed` maps it to the installed view:
+Z up, the backboard behind it at -X, and the ball leaving toward +X.
"""

from __future__ import annotations

import math

from manifold3d import CrossSection, Manifold

from .base import BuildResult, Param, Part, Template, pack_plates

SEG = 96
CHUTE_COLOR = "#5b5f66"
HANGER_COLOR = "#2b2b2b"
SIDE_CLEARANCE = 5.0  # room each side of the ball between the side panels
DEPTH_TOP = 0.6  # side panel depth at the top, as a fraction of the ball diameter
DEPTH_END = 0.42  # ...tapering to this at the spout (sloped side profile)
LIP_H = 4.0  # inward lip along the side panels' open edges, leaning forward at 45 degrees
LIP_T = 2.0
BEAD = 3.0  # glue bead along the back seam (sticks out this far behind the floor)
PIN_R = 0.95  # holes for 1.75 mm filament alignment pins
PIN_DEPTH = 3.0  # per half
SCREW_R = 1.7  # M3
# Hanger: caps the block where the rim meets the backboard.
CAP_FIT = 0.4  # clearance around the block
CAP_T = 2.4  # cap wall thickness
FINGER = 6.0  # size of the two front fingers that stop the cap sliding off the block
LEG_W = 10.0  # leg / spine width
LEG_T = 4.0  # leg thickness (lies flat against the backboard)
BLOCK_H = 24.0  # the block at the bottom that the chute screws to
BLOCK_W = 52.0
GUSSET = 35.0  # support triangles from the spine down onto the block
GUSSET_T = 3.0
SCREW_SPREAD = 36.0  # chute-to-hanger screws, side to side
SCREW_DOWN = (6.0, 18.0)  # ...and how far below the top of the chute
TAP_R = 1.35  # M3 screws thread straight into the plastic (2.7 mm pilot hole)


def _poly(points) -> CrossSection:
    """CrossSection from one polygon, in either winding order."""
    area = 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        area += x1 * y2 - x2 * y1
    return CrossSection([points if area > 0 else points[::-1]])


class CurvedReturnTemplate(Template):
    name = "Curved ball return (store style)"
    description = (
        "Curved open-frame chute that hangs from the block where the rim meets the backboard, "
        "catches the ball under the net, and sends it back to you. Every part prints without supports."
    )
    params = [
        Param("ball_diameter", "Ball diameter", 80, 40, 130,
              help="Default fits an 80 mm mini airless ball. Measure yours."),
        Param("bend_radius", "Bend radius (0 = auto)", 0, 0, 250,
              help="Radius of the chute's floor through the turn. 0 picks the smallest bend that "
                   "still catches the ball under the rim centre."),
        Param("bend_angle", "Bend angle", 65, 30, 90, unit="deg",
              help="How far the chute turns from straight down. 65 means the exit slopes 25 degrees downhill toward you."),
        Param("lead_in", "Straight section at top", 40, 32, 100,
              help="Straight drop at the top of the chute. The hanger bolts to its upper part."),
        Param("exit_length", "Spout length", 35, 0, 150,
              help="Straight run after the turn. The end of it is rounded off into the spout."),
        Param("wall", "Wall thickness", 2.0, 1.6, 5),
        Param("block_width", "Rim block width", 57.2, 20, 150,
              help="Side to side, along the backboard (2.25 in = 57.2 mm)."),
        Param("block_depth", "Rim block depth", 25.4, 5, 80,
              help="How far it sticks out from the backboard (1 in = 25.4 mm)."),
        Param("block_height", "Rim block height", 12.7, 5, 80,
              help="Top to bottom (0.5 in = 12.7 mm)."),
        Param("standoff", "Chute gap from backboard", 20, 8, 80,
              help="How far the back of the chute sits out from the backboard."),
        Param("board_to_center", "Backboard to rim centre", 110, 60, 300,
              help="Straight out from the backboard to the middle of the rim. The ball drops here."),
        Param("rim_diameter", "Rim inside diameter", 150, 80, 400,
              help="Across the inside of the rim. Used to check the spout doesn't stick out past "
                   "the front of the rim."),
        Param("drop", "Block to chute drop", 100, 40, 400,
              help="From the bottom of the rim block down to the top of the chute. Make it longer "
                   "than the net so the ball falls out of the net first."),
        Param("bed_size", "Printer bed size", 256, 150, 400,
              help="256 for Bambu X1/P1/P2, 180 for the A1 mini."),
    ]

    def _chute(self, v):
        """Build one chute half (print-ready) and the full chute (for the installed view).

        Cross-section (print frame, r = distance from the bend axis, z = up): a U channel with
        a flat floor on the outside of the bend and two flat side panels. It is split down the
        middle of the floor (z = zc) into two identical halves. Each half prints lying on its
        side panel: a flat plate (big footprint, windows need no bridging) with the half floor
        rising from it as a short vertical wall. A slim glue bead along the back rejoins the halves.
        """
        t = v["wall"]
        ball = v["ball_diameter"]
        w_in = ball + 2 * SIDE_CLEARANCE  # inside width between the side panels
        depth = DEPTH_TOP * ball  # side panels reach this far in from the floor at the top...
        depth_end = DEPTH_END * ball  # ...and taper to this at the spout
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
        rc = min(depth_end + t, exit_len) if exit_len > 0 else 0
        if exit_len > 0:
            ext = Manifold.extrude(profile, exit_len + 0.5)  # 0.5 mm overlap fuses it to the bend
            # Rounded spout: the side panel curves down to the floor along a quarter circle.
            # The cut is vertical while printing, so it adds no overhang.
            keep = Manifold.cube([rf + t + 10, zc + 4, exit_len + 1]).translate([0, -2, rc])
            keep = keep + Manifold.cylinder(zc + 4, rc, circular_segments=SEG).rotate(
                [-90, 0, 0]).translate([rf + t, -2, rc])
            half = half + self._exit(ext ^ keep, exit_len, angle)

        # Sloped side profile: the panels' open edge runs from `depth` at the top down to
        # `depth_end` at the spout. Path position p is measured along the floor from the start
        # of the bend (negative up the lead-in). The cut is vertical as printed.
        th = math.radians(angle)
        arc = rf * th
        total = arc + exit_len

        def depth_at(p):
            return depth if p <= 0 else depth + (depth_end - depth) * min(p / total, 1.0)

        def point(p, r_off):  # point on the path at p, r_off from the bend axis side of the floor
            if p <= 0:
                return (r_off, p)
            if p <= arc:
                a = p / rf
                return (r_off * math.cos(a), r_off * math.sin(a))
            w = p - arc
            return (r_off * math.cos(th) - w * math.sin(th), r_off * math.sin(th) + w * math.cos(th))

        steps = [(-lead_len - 2) + i * 2.0 for i in range(int((total + lead_len + 4) / 2) + 1)]
        edge = [point(p, rf - depth_at(p)) for p in steps]
        outer = [point(p, rf + 40) for p in reversed(steps)]
        keep = Manifold.extrude(_poly(edge + outer), zc + 2).translate([0, 0, -1])
        half = half ^ keep

        # Lip along the open edge: a small fin on the panel leaning 45 degrees inward and
        # forward (a 45 degree overhang as printed). It stops where the spout rounds off.
        def inward(x, y):  # unit vector from the floor toward the open side, at (x, y)
            if y < 0:
                return (-1.0, 0.0)
            if math.atan2(y, x) <= th:
                r = math.hypot(x, y)
                return (-x / r, -y / r)
            return (-math.cos(th), -math.sin(th))

        lip_steps = [p for p in steps if -lead_len <= p <= total - rc]
        band = ([point(p, rf - depth_at(p)) for p in lip_steps]
                + [point(p, rf - depth_at(p) + LIP_T + 1.0) for p in reversed(lip_steps)])
        fin = Manifold.extrude(_poly(band), LIP_H + 0.01).translate([0, 0, t - 0.01])

        def lean(pt):
            x, y, z = pt
            k = max(0.0, z - t)
            nx, ny = inward(x, y)
            return [x + nx * k, y + ny * k, z]

        half = half + fin.refine_to_length(4.0).warp(lean)

        # Windows in the side panel (flat on the plate, so any size prints cleanly); each one
        # follows the sloped edge.
        mw = 6.0
        r_mid = rf - depth / 2
        win_deg, rib_deg = math.degrees(24.0 / r_mid), math.degrees(8.0 / r_mid)
        pitch = win_deg + rib_deg
        nw = max(0, int((angle - rib_deg) // pitch))
        w0 = (angle - nw * pitch + rib_deg) / 2
        for i in range(nw):
            a_mid = w0 + i * pitch + win_deg / 2
            d = depth_at(rf * math.radians(a_mid + win_deg / 2))  # shallowest end of this window
            win_i = _poly([(rf - d + mw, -1), (rf - mw, -1), (rf - mw, t + 1), (rf - d + mw, t + 1)])
            half = half - Manifold.revolve(win_i, 8, win_deg).rotate([0, 0, w0 + i * pitch])

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
            d = depth_at(arc + pos + 10)
            win = _poly([(rf - d + mw, -1), (rf - mw, -1), (rf - mw, t + 1), (rf - d + mw, t + 1)])
            cut = floor_cut + win if pos + 10 <= rounded_from - 3 else floor_cut
            half = half - self._exit(Manifold.extrude(cut, 10.0).translate([0, 0, -(pos + 10)]), 0, angle)
            pos += 16.0

        # Slim glue bead along the back seam (half of it on each half): a 45 degree triangle,
        # so it prints unsupported. Holes for 1.75 mm filament pins line the halves up.
        bead = _poly([(rf + t - 0.3, zc - BEAD - 0.3), (rf + t + BEAD, zc), (rf + t - 0.3, zc)])
        half = half + Manifold.revolve(bead, SEG, angle)
        lead_bead = lead_len - BLOCK_H - 1  # stop below the hanger's block
        if lead_bead > 0:
            half = half + along_lead(Manifold.extrude(bead, lead_bead + 0.5).translate([0, 0, -0.5]))
        if exit_len > 0:
            half = half + self._exit(Manifold.extrude(bead, exit_len + 0.5), exit_len, angle)
        r_pin = rf + t + 0.3
        pin = Manifold.cylinder(PIN_DEPTH + 1, PIN_R, circular_segments=16)
        for frac in (0.15, 0.5, 0.85):
            a = math.radians(angle * frac)
            half = half - pin.translate([r_pin * math.cos(a), r_pin * math.sin(a), zc - PIN_DEPTH])

        # Screw holes through the floor near the top: the hanger's block screws on here
        # (two M3 per half, 4 in all).
        z_screw = zc - SCREW_SPREAD / 2
        for down in SCREW_DOWN:
            half = half - Manifold.cylinder(t + 4, SCREW_R, circular_segments=16).rotate(
                [0, 90, 0]).translate([rf - 2, -(lead_len - down), z_screw])

        full = half + half.mirror([0, 0, 1]).translate([0, 0, 2 * zc])
        geo = dict(t=t, rf=rf, zc=zc, w_in=w_in, depth=depth)
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

    # ----------------------------------------------------------------- hanger
    def _hanger(self, v, x_board, x_floor, z_top, screws):
        """One-piece hanger in the installed frame. Prints lying on its backboard side.

        x_floor is the back face of the chute floor and z_top the top of the chute.
        """
        bw, bd, bh = v["block_width"], v["block_depth"], v["block_height"]
        f, t = CAP_FIT, CAP_T
        zb = z_top + v["drop"]  # bottom of the rim block
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

        # Two legs down past the block ends, joining into one spine (a flat profile on the board).
        z_bb = z_top - BLOCK_H  # bottom of the screw block
        z_join = zb - 30
        legs = CrossSection()
        for sgn in (1, -1):
            yl = sgn * (yo + LEG_W / 2)
            legs = legs + CrossSection.batch_hull([
                CrossSection.square([LEG_W, 1], center=True).translate([yl, zb + 0.4 * bh + 0.5]),
                CrossSection.square([LEG_W, 1], center=True).translate([yl, zb - 6]),
            ])
            legs = legs + CrossSection.batch_hull([
                CrossSection.circle(LEG_W / 2, 24).translate([yl, zb - 6]),
                CrossSection.circle(LEG_W / 2, 24).translate([0, z_join]),
            ])
        z_flare = z_top + GUSSET
        legs = legs + CrossSection.square([LEG_W, z_join - z_flare]).translate([-LEG_W / 2, z_flare])
        legs = legs + CrossSection.batch_hull([  # spine widens onto the block
            CrossSection.square([LEG_W, 1]).translate([-LEG_W / 2, z_flare]),
            CrossSection.square([BLOCK_W, 1]).translate([-BLOCK_W / 2, z_top - 1]),
        ])
        # local (u, w, e) -> (x = xo + e, y = u, z = w)
        spine = Manifold.extrude(legs, LEG_T).transform([[0, 0, 1, xo], [1, 0, 0, 0], [0, 1, 0, 0]])

        # Block from the board to the back of the chute. It's solid where the screws go, with two
        # pockets from the board side to save plastic (their 10 mm roofs bridge easily).
        shelf = Manifold.cube([x_floor - xo, BLOCK_W, BLOCK_H]).translate([xo, -BLOCK_W / 2, z_bb])
        for y0 in (-11.0, 1.0):
            shelf = shelf - Manifold.cube([x_floor - xo - 4, 10, BLOCK_H - 6]).translate(
                [xo - 1, y0, z_bb + 3])
        # Support triangles tying the spine to the top of the block, along both spine edges.
        tri = _poly([(xo, z_top - 0.5), (x_floor, z_top - 0.5), (xo, z_top + GUSSET)])
        for y in (-LEG_W / 2, LEG_W / 2 - GUSSET_T):
            # local (x, z_profile, w) -> (X = x, Y = y + w, Z = z_profile)
            shelf = shelf + Manifold.extrude(tri, GUSSET_T).transform(
                [[1, 0, 0, 0], [0, 0, 1, y], [0, 1, 0, 0]])
        for y, z in screws:  # pilot holes: M3 screws thread in from inside the chute
            shelf = shelf - Manifold.cylinder(x_floor - xo + 2, TAP_R, circular_segments=16).rotate(
                [0, 90, 0]).translate([xo + 4, y, z])
        return cap + spine + shelf

    @staticmethod
    def catch_reach(v, rf):
        """How far in front of the floor's top (inner face) the floor reaches at the spout end."""
        a = math.radians(v["bend_angle"])
        return rf * (1 - math.cos(a)) + v["exit_length"] * math.sin(a)

    def auto_bend_radius(self, v):
        """Smallest bend that puts floor under the falling ball (centre plus a 30% margin)."""
        need = v["board_to_center"] - v["standoff"] - v["wall"] + 0.3 * v["ball_diameter"] / 2
        a = math.radians(v["bend_angle"])
        rf = (need - v["exit_length"] * math.sin(a)) / (1 - math.cos(a))
        return max(50.0, math.ceil(rf / 5) * 5)

    # ------------------------------------------------------------------ build
    def build(self, v: dict[str, float]) -> BuildResult:
        v = dict(v)
        auto = v["bend_radius"] < 50
        if auto:
            v["bend_radius"] = self.auto_bend_radius(v)
        half, chute, geo = self._chute(v)
        chute_inst = self._to_installed(chute, geo["zc"])

        t, rf = geo["t"], geo["rf"]
        z_top = v["lead_in"]  # top of the chute in the installed frame
        x_floor = -(rf + t)  # back face of the chute floor
        x_board = x_floor - v["standoff"]
        x_catch = x_board + v["board_to_center"]  # the ball drops here, under the rim centre
        if x_catch - v["ball_diameter"] / 2 < -rf + 2:
            raise ValueError("Backboard to rim centre is too short: the ball would miss the chute "
                             "(it would fall behind it). Reduce the chute gap from the backboard.")
        screws = [(y, z_top - d) for y in (SCREW_SPREAD / 2, -SCREW_SPREAD / 2) for d in SCREW_DOWN]
        hanger = self._hanger(v, x_board, x_floor, z_top, screws)

        zb = z_top + v["drop"]
        blk = Manifold.cube([v["block_depth"], v["block_width"], v["block_height"]]).translate(
            [x_board, -v["block_width"] / 2, zb])
        board = Manifold.cube([2, 200, zb + 140]).translate([x_board - 2, -100, -120])
        assembled = [
            Part("Chute", chute_inst, CHUTE_COLOR),
            Part("Hanger", hanger, HANGER_COLOR),
            Part("Rim block", blk, "#ff5a1f"),  # preview only
            Part("Backboard", board, "#e8e8e8"),  # preview only
        ]

        bed = v["bed_size"]
        best = None
        # The chute goes out as ONE part lying on a side panel. Cut it in Bambu Studio with a flat
        # cut at half its height to get the two identical halves.
        for spin in range(0, 180, 15):  # try turning the parts on the plate
            c = chute.rotate([0, 0, spin])
            for hspin in (0, 90):
                hg = hanger.rotate([0, -90, 0]).rotate([0, 0, hspin])  # backboard side down
                result = pack_plates([Part("Chute", c, CHUTE_COLOR),
                                      Part("Hanger", hg, HANGER_COLOR)], bed)
                if best is None or result[1] < best[1]:
                    best = result
            if best[1] == 1:
                break
        print_parts, n_plates = best

        notes = []
        if n_plates > 1:
            notes.append(f"Needs {n_plates} plates on a {bed:.0f} mm bed. The file lays them out side "
                         "by side. In Bambu Studio add a plate and press A (Arrange), and it will "
                         "split them.")
        for p in print_parts:
            sx, sy, sz = p.size()
            if max(sx, sy) > bed or sz > bed:
                notes.append(f"Warning: the {p.name.lower()} is {sx:.0f} x {sy:.0f} x {sz:.0f} mm, "
                             f"larger than your {bed:.0f} mm bed."
                             + (" Shorten the block-to-chute drop." if p.name == "Hanger" else ""))
        reach = x_floor + t + self.catch_reach(v, rf) - x_board  # floor at the spout end, from the board
        ball_needs = v["board_to_center"] + 0.3 * v["ball_diameter"] / 2
        if reach < ball_needs - 0.5:
            notes.append(f"Warning: the ball drops {v['board_to_center']:.0f} mm out from the backboard, "
                         f"but the chute floor only reaches {reach:.0f} mm, so the ball could miss it. "
                         "Use a bigger bend radius (or 0 for automatic), a longer spout, or a "
                         "bigger gap from the backboard.")
        else:
            notes.append(f"Bend radius {'(automatic) ' if auto else ''}{rf:.0f} mm: the ball lands "
                         f"on the curve about {v['board_to_center']:.0f} mm out from the backboard.")
        tip = chute_inst.bounding_box()[3] - x_board
        rim_front = v["board_to_center"] + v["rim_diameter"] / 2
        if tip > rim_front:
            notes.append(f"Warning: the spout reaches {tip:.0f} mm out from the backboard, "
                         f"{tip - rim_front:.0f} mm past the front of the rim. Use a smaller bend "
                         "radius, bend angle or spout length.")
        else:
            notes.append(f"The spout reaches {tip:.0f} mm out from the backboard, "
                         f"{rim_front - tip:.0f} mm inside the front of the rim.")
        notes.append(
            f"Bambu Studio: the chute comes in as one part lying on a side panel. Split it with the "
            f"Cut tool at Z = {geo['zc']:.1f} mm, which is exactly half its height. Flip the upper "
            "part so both halves lie on their side panels. Then supports OFF. The hanger lies on "
            "its backboard side. PETG or PLA."
        )
        notes.append(
            "Joining the halves: push three short pieces of 1.75 mm filament (about 6 mm long) into "
            "the pin holes along the seam, then glue the halves floor to floor. Use CA (super) glue "
            "for PLA, or a plastic cement for PETG, along the floor edge and the bead on the back. "
            "The hanger's 4 screws also clamp both halves together at the top."
        )
        notes.append(
            "Hanging: press the hanger's cap down over the block where the rim joins the "
            "backboard. Its two legs run down the board past the block ends. Bolt the top of the "
            "chute to the hanger's block with 4 M3 x 16 mm screws, 2 per half. Drive them from "
            "inside the chute so they thread straight into the block (2.7 mm pilot holes, no nuts). "
            "The block also holds the two halves together at the top. Measure the block, the board-to-rim-centre distance and your "
            "net length first, because the cap is a snug 0.4 mm fit."
        )
        return BuildResult(assembled, print_parts, notes)
