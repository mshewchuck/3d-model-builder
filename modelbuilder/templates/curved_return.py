"""Curved ball return in the style of store-bought hoop returns.

Parts (all print with no supports):
* Chute, in two identical halves: a U channel that bends (70 degrees by default, so the exit runs
  downhill) with a slotted floor, flat side panels with windows, and a rounded spout. Each half
  prints lying flat on its side panel. Ears along the back join the halves.
* Hanger: caps the block where the rim joins the backboard, runs down the board as a ladder
  frame, and ends in two cheeks that clamp the outside of the chute's side panels (3 M3
  screws each, loaded in shear). Prints lying on its backboard side.

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
CATCH_GAP = 20.0  # the falling ball's back passes this far in front of the chute floor
EAR = 6.0  # how far the joining ears stick out behind the floor
EAR_W = 12.0  # ear width along the chute
EAR_HOLE_R = 1.7  # M3 screw or a small zip tie
SCREW_R = 1.7  # M3
# Hanger: caps the block where the rim meets the backboard.
CAP_FIT = 0.4  # clearance around the block
CAP_T = 2.4  # cap wall thickness
FINGER = 6.0  # size of the two front fingers that stop the cap sliding off the block
LEG_W = 10.0  # leg width
LEG_T = 4.0  # leg / frame thickness (lies flat against the backboard)
BAR_W = 8.0  # cross bars tying the two legs into a ladder frame
CHEEK_H = 24.0  # height of the cheeks where they clamp the chute
CHEEK_UP = 30.0  # the cheeks rise this far up the frame at the backboard (a brace)
CHEEK_T = 3.0
CHEEK_REACH = 36.0  # how far the cheeks reach forward along the chute's side panels
CHEEK_FIT = 0.3
SIDE_SCREW_X = (8.0, 19.0, 30.0)  # side screws: distance in front of the chute floor
SIDE_SCREW_DOWN = 12.0  # ...and below the top of the chute


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
        Param("bend_radius", "Bend radius", 70, 50, 200,
              help="Radius of the chute's floor through the turn. Bigger turns more smoothly but is bigger to print."),
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
        Param("board_to_center", "Backboard to rim centre", 110, 60, 300,
              help="Straight out from the backboard to the middle of the rim. The ball drops here."),
        Param("rim_diameter", "Rim inside diameter", 150, 80, 400,
              help="Across the inside of the rim. Used to check the spout doesn't stick out past "
                   "the front of the rim."),
        Param("drop", "Block to chute drop", 170, 60, 400,
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
        for frac in (0.1, 0.3, 0.5, 0.7, 0.9):
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

        # (No ear on the lead-in: the hanger's cheeks clamp both halves there.)
        if exit_len - rc >= EAR_W + 4:
            half = half + self._exit(straight_ear(lambda m: m, -(exit_len - rc) / 2), 0, angle)

        # Screw holes through the side panel near the top, where the hanger's cheeks clamp it.
        for dx in SIDE_SCREW_X:
            half = half - Manifold.cylinder(t + 2, SCREW_R, circular_segments=16).translate(
                [rf + t - dx, -(lead_len - SIDE_SCREW_DOWN), -1])

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
    def _hanger(self, v, x_board, x_floor, z_top, y_side):
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

        # Ladder frame flat on the board: two straight legs from the end plates down to the
        # cheeks, tied by cross bars. Drawn as a (y, z) profile and extruded LEG_T from the board.
        z_cb = z_top - CHEEK_H  # bottom of the cheeks
        z_up = z_top + CHEEK_UP  # top of the cheeks' brace at the board
        yl = yo + LEG_W / 2  # leg centres, just outside the block ends
        y_cheek = y_side + CHEEK_FIT + CHEEK_T / 2  # centre of each cheek
        wide = 2 * (y_cheek + CHEEK_T / 2)
        span = 2 * yl + LEG_W
        frame = CrossSection()
        for sgn in (1, -1):
            frame = frame + CrossSection.square([LEG_W, zb + 0.4 * bh + 2 - z_cb]).translate(
                [sgn * yl - LEG_W / 2, z_cb])
            frame = frame + CrossSection.square([CHEEK_T + 4, z_up - z_cb]).translate(
                [sgn * y_cheek - (CHEEK_T + 4) / 2, z_cb])  # upright under each cheek
        for zbar, w in ((z_cb, wide), (z_up - BAR_W, wide), ((z_up + zb) / 2 - BAR_W / 2, span),
                        (zb - BAR_W - 4, span)):
            frame = frame + CrossSection.square([w, BAR_W]).translate([-w / 2, zbar])
        # local (u, w, e) -> (x = xo + e, y = u, z = w)
        spine = Manifold.extrude(frame, LEG_T).transform([[0, 0, 1, xo], [1, 0, 0, 0], [0, 1, 0, 0]])

        # Two cheeks run from the frame out along the outside of the chute's side panels and
        # bolt to them with 3 screws each. They are vertical walls as printed (no supports).
        cheek_prof = _poly([(xo, z_cb), (x_floor + CHEEK_REACH, z_cb), (x_floor + CHEEK_REACH, z_top),
                            (xo + LEG_T, z_up), (xo, z_up)])
        shelf = Manifold()
        for sgn in (1, -1):
            # local (x, z_profile, w) -> (X = x, Y = y + T/2 - w, Z = z_profile)
            shelf = shelf + Manifold.extrude(cheek_prof, CHEEK_T).transform(
                [[1, 0, 0, 0], [0, 0, -1, sgn * y_cheek + CHEEK_T / 2], [0, 1, 0, 0]])
        for dx in SIDE_SCREW_X:
            hole = Manifold.cylinder(2 * y_cheek + 10, SCREW_R, circular_segments=16).rotate([90, 0, 0])
            shelf = shelf - hole.translate([x_floor + dx, y_cheek + 5, z_top - SIDE_SCREW_DOWN])
        return cap + spine + shelf

    # ------------------------------------------------------------------ build
    def build(self, v: dict[str, float]) -> BuildResult:
        half, chute, geo = self._chute(v)
        chute_inst = self._to_installed(chute, geo["zc"])

        t, rf = geo["t"], geo["rf"]
        z_top = v["lead_in"]  # top of the chute in the installed frame
        x_floor = -(rf + t)  # back face of the chute floor
        x_catch = -rf + v["ball_diameter"] / 2 + CATCH_GAP  # where the ball drops (under the rim centre)
        x_board = x_catch - v["board_to_center"]
        if x_floor - x_board < 12:
            raise ValueError("Backboard to rim centre is too short: the chute would hit the backboard.")
        y_side = geo["zc"]  # outer face of each side panel (installed |Y|)
        hanger = self._hanger(v, x_board, x_floor, z_top, y_side)

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
        for spin in range(0, 180, 15):  # try turning the parts on the plate
            h = half.rotate([0, 0, spin])
            for hspin in (0, 90):
                hg = hanger.rotate([0, -90, 0]).rotate([0, 0, hspin])  # backboard side down
                result = pack_plates([Part("Chute half A", h, CHUTE_COLOR),
                                      Part("Chute half B", h, CHUTE_COLOR),
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
            "Bambu Studio: supports OFF. The chute is two identical halves, each lying flat on its "
            "side panel. The hanger lies on its backboard side. PETG or PLA."
        )
        notes.append(
            "Joining the halves: put them together floor to floor. The 6 ears along the back pair "
            "up. Put an M3 x 20 mm screw and nut, or a small zip tie, through each pair."
        )
        notes.append(
            "Hanging: press the hanger's cap down over the block where the rim joins the "
            "backboard. Its two legs run down the board past the block ends. Bolt the top of the "
            "chute between the hanger's two cheeks with 6 M3 x 8 mm screws and nuts (3 per side, "
            "heads outside, nuts inside). The screws carry the chute's weight sideways (in shear), "
            "which is far stronger than pulling straight out, and the cheeks hold the two halves "
            "together at the top. Measure the block, the board-to-rim-centre distance and your "
            "net length first, because the cap is a snug 0.4 mm fit."
        )
        return BuildResult(assembled, print_parts, notes)
