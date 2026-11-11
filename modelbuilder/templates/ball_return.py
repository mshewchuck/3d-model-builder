"""Ball return chute for a small (mini / over-the-door) basketball hoop.

Design
------
* Chute: a U-shaped half-pipe with a closed back end. It sits under the net,
  catches the ball, and rolls it back out the front at the chosen slope.
* Two hangers: flat plates that snap onto the rim tube with an upward-facing
  C-clip and bolt to mounting fins on each side of the chute (2x M4 each).

The parts print separately so every piece fits a 256 mm Bambu plate. The
hangers print flat with no supports; the chute prints standing on its closed
end (enable supports for the two mounting fins).

Coordinates in the assembled view: +X is toward the shooter (downhill),
Z is up, the rim centre sits above the catch point of the chute.
"""

from __future__ import annotations

import math

from manifold3d import CrossSection, Manifold

from .base import BuildResult, Param, Part, Template, lay_out_on_plate, plate_footprint

SEGMENTS = 96
FIN_THICKNESS = 6.0  # along X
PAD_WIDTH = 20.0  # how far the fin/pad sticks out past the chute wall
FIN_HEIGHT = 35.0  # fin height above the chute's top edge
FIN_OVERLAP = 12.0  # fin extends this far below the top edge to fuse with the wall
CLIP_WALL = 4.0
CLIP_FIT = 0.25  # radial clearance around the rim tube


class BallReturnTemplate(Template):
    name = "Mini hoop ball return"
    description = (
        "Chute that hangs under a mini basketball hoop's net and rolls the ball back to you. "
        "Measure your ball, rim and net, then adjust the numbers."
    )
    params = [
        Param("ball_diameter", "Ball diameter", 130, 60, 250,
              help="Mini balls are usually 5 in (127 mm) or 7 in (178 mm)."),
        Param("clearance", "Ball clearance (each side)", 8, 2, 30,
              help="Extra room so the ball rolls freely in the chute."),
        Param("wall", "Wall thickness", 3, 2, 8),
        Param("chute_length", "Chute length", 200, 100, 250,
              help="Prints standing up, so keep it under your printer's height."),
        Param("slope_deg", "Chute slope", 15, 5, 40, unit="deg",
              help="Steeper sends the ball back faster."),
        Param("rim_inner_diameter", "Rim inside diameter", 230, 120, 460,
              help="Measure across the inside of the rim. Mini hoops are often 9 in (229 mm)."),
        Param("rim_tube_diameter", "Rim tube diameter", 12, 5, 30,
              help="Thickness of the rim's metal tube (calipers work best)."),
        Param("rim_drop", "Rim to chute height", 150, 60, 400,
              help="Vertical gap from the rim down to the chute's top edge. Must be longer than the net."),
        Param("hanger_thickness", "Hanger thickness", 8, 4, 15),
        Param("bolt_diameter", "Bolt hole diameter", 4.5, 2.5, 8,
              help="4.5 mm fits M4 bolts."),
        Param("bed_size", "Printer bed size", 256, 150, 400,
              help="256 for Bambu X1/P1/P2, 180 for the A1 mini."),
    ]

    def build(self, v: dict[str, float]) -> BuildResult:
        ball_r = v["ball_diameter"] / 2
        wall = v["wall"]
        length = v["chute_length"]
        slope = v["slope_deg"]
        r_in = ball_r + v["clearance"]
        r_out = r_in + wall
        notes: list[str] = []

        # ---- Chute (in its own frame: axis along +X, open side up, top edge at z=0)
        outer = Manifold.cylinder(length, r_out, circular_segments=SEGMENTS).rotate([0, 90, 0])
        inner = (
            Manifold.cylinder(length, r_in, circular_segments=SEGMENTS)
            .rotate([0, 90, 0])
            .translate([wall, 0, 0])
        )
        top_cut = Manifold.cube([length + 20, 2 * r_out + 20, r_out + 20]).translate(
            [-10, -r_out - 10, 0]
        )
        chute = outer - inner - top_cut

        # Tilt so the far end runs downhill toward +X.
        chute = chute.rotate([0, slope, 0])
        s, c = math.sin(math.radians(slope)), math.cos(math.radians(slope))
        catch_x = wall + r_in  # where the ball lands, in the chute frame
        xw, zw = catch_x * c, -catch_x * s  # same point in the assembled frame

        # ---- Mounting fins (vertical in the assembled frame), both sides
        fin = Manifold.cube(
            [FIN_THICKNESS, (r_out + PAD_WIDTH) - r_in, FIN_HEIGHT + FIN_OVERLAP]
        ).translate([xw - FIN_THICKNESS / 2, r_in, zw - FIN_OVERLAP])
        hole_y = r_out + PAD_WIDTH / 2
        hole_zs = [zw + 10, zw + FIN_HEIGHT - 10]
        bolt_r = v["bolt_diameter"] / 2
        for hz in hole_zs:
            hole = (
                Manifold.cylinder(FIN_THICKNESS + 2, bolt_r, circular_segments=32)
                .rotate([0, 90, 0])
                .translate([xw - FIN_THICKNESS / 2 - 1, hole_y, hz])
            )
            fin = fin - hole
        chute = chute + fin + fin.mirror([0, 1, 0])

        # ---- Hanger profile in the (radial u = Y, vertical v = Z) plane
        tube_r = v["rim_tube_diameter"] / 2
        clip_ri = tube_r + CLIP_FIT
        clip_ro = clip_ri + CLIP_WALL
        clip_u = v["rim_inner_diameter"] / 2 + tube_r
        clip_v = zw + v["rim_drop"]

        pad = CrossSection.square([PAD_WIDTH, FIN_HEIGHT]).translate([r_out, zw])
        pad_top = CrossSection.square([PAD_WIDTH, 6]).translate([r_out, zw + FIN_HEIGHT - 6])
        ring = CrossSection.circle(clip_ro, SEGMENTS).translate([clip_u, clip_v])
        strut = CrossSection.batch_hull([pad_top, ring])
        profile = pad + strut
        profile = profile - CrossSection.circle(clip_ri, SEGMENTS).translate([clip_u, clip_v])
        gap = tube_r * 1.6  # snap opening, narrower than the tube
        profile = profile - CrossSection.square([gap, clip_ro + 1]).translate(
            [clip_u - gap / 2, clip_v]
        )
        for hz in hole_zs:
            profile = profile - CrossSection.circle(bolt_r, 32).translate([hole_y, hz])

        ht = v["hanger_thickness"]
        hanger_flat = Manifold.extrude(profile, ht)
        # Map local (u, v, w) -> assembled (x = fin face + w, y = u, z = v).
        hanger_right = hanger_flat.transform(
            [[0, 0, 1, xw + FIN_THICKNESS / 2], [1, 0, 0, 0], [0, 1, 0, 0]]
        )
        hanger_left = hanger_right.mirror([0, 1, 0])

        assembled = [
            Part("Chute", chute, "#e07b39"),
            Part("Hanger (right)", hanger_right, "#3a7bd5"),
            Part("Hanger (left)", hanger_left, "#3a7bd5"),
        ]

        # ---- Print layout: chute back to level, then stood on its closed end.
        chute_print = chute.rotate([0, -slope, 0]).rotate([0, -90, 0])
        print_parts = lay_out_on_plate(
            [
                Part("Chute", chute_print, "#e07b39"),
                Part("Hanger A", hanger_flat, "#3a7bd5"),
                Part("Hanger B", hanger_flat, "#3a7bd5"),
            ]
        )

        bed = v["bed_size"]
        fx, fy, fz = plate_footprint(print_parts)
        if max(fx, fy) > bed or fz > bed:
            notes.append(
                f"Warning: the plate layout is {fx:.0f} x {fy:.0f} x {fz:.0f} mm, larger than your "
                f"{bed:.0f} mm bed. Shorten the chute or rim drop, or use a smaller ball/clearance. "
                "You can also print the parts on separate plates in Bambu Studio."
            )
        if clip_u < r_out + PAD_WIDTH / 2:
            notes.append("Note: the rim is narrower than the chute, so the hangers lean inward.")
        notes.append(
            "Hardware: 4x M4 x 20 mm bolts with nuts. Snap the clips onto the rim between net hooks."
        )
        notes.append(
            "Bambu Studio: hangers print flat with no supports. Turn on supports "
            "(tree, build plate only) for the chute's mounting fins."
        )
        return BuildResult(assembled, print_parts, notes)
