"""Ball return tray for a small (mini / over-the-door) basketball hoop.

One flat part, no supports, no bolts: a thin floor with low side rails and a
back stop. Hang it under the net with zip ties (or cord) through the slots:
back corners higher than the front so the ball rolls back to you.

Print orientation = installed orientation (floor on the bed). +X runs from the
back stop toward the open front end.
"""

from __future__ import annotations

from manifold3d import Manifold

from .base import BuildResult, Param, Part, Template, lay_out_on_plate, plate_footprint

TIE_SLOT = (4.0, 8.0)  # zip-tie slot size (along X, along Y)


class BallReturnTemplate(Template):
    name = "Mini hoop ball return"
    description = (
        "Single flat tray that hangs under a mini hoop's net with zip ties and rolls the ball "
        "back to you. Prints flat with no supports."
    )
    params = [
        Param("ball_diameter", "Ball diameter", 130, 60, 250,
              help="Mini balls are usually 5 in (127 mm) or 7 in (178 mm)."),
        Param("clearance", "Ball clearance (each side)", 8, 2, 30,
              help="Extra room so the ball rolls freely between the rails."),
        Param("length", "Tray length", 200, 100, 400,
              help="Keep it under your bed size."),
        Param("rail_height", "Side rail height", 25, 10, 60,
              help="Low rails keep the ball on track and save plastic."),
        Param("floor", "Floor thickness", 2.4, 1.2, 6),
        Param("wall", "Rail thickness", 2.0, 1.2, 6),
        Param("cutouts", "Floor cutouts (1 = on, 0 = off)", 1, 0, 1, unit="",
              help="Slots in the floor along the rolling direction. Saves about a third of the plastic."),
        Param("bed_size", "Printer bed size", 256, 150, 400,
              help="256 for Bambu X1/P1/P2, 180 for the A1 mini."),
    ]

    def build(self, v: dict[str, float]) -> BuildResult:
        inner_w = v["ball_diameter"] + 2 * v["clearance"]
        wall, floor_t = v["wall"], v["floor"]
        length, rail_h = v["length"], v["rail_height"]
        width = inner_w + 2 * wall

        tray = Manifold.cube([length, width, floor_t])
        rail = Manifold.cube([length, wall, rail_h])
        tray = tray + rail + rail.translate([0, width - wall, 0])
        tray = tray + Manifold.cube([wall, width, rail_h])  # back stop

        # Lightening slots run along the rolling direction so the ball rides the ribs.
        margin = 15.0
        if v["cutouts"] >= 0.5:
            slot_w, rib = 10.0, 10.0
            span = inner_w - 2 * margin
            count = int((span + rib) // (slot_w + rib))
            if count > 0:
                used = count * slot_w + (count - 1) * rib
                y0 = wall + (inner_w - used) / 2
                slot_len = length - wall - 2 * margin
                for i in range(count):
                    tray = tray - Manifold.cube([slot_len, slot_w, floor_t + 2]).translate(
                        [wall + margin, y0 + i * (slot_w + rib), -1]
                    )

        # Zip-tie slots through the floor, just inside each rail: two at the back, two near the front.
        sx, sy = TIE_SLOT
        for x in (wall + 6, length - 6 - sx):
            for y in (wall + 3, width - wall - 3 - sy):
                tray = tray - Manifold.cube([sx, sy, floor_t + 2]).translate([x, y, -1])

        part = Part("Ball return tray", tray, "#e07b39")
        print_parts = lay_out_on_plate([part])

        notes = []
        bed = v["bed_size"]
        fx, fy, fz = plate_footprint(print_parts)
        if max(fx, fy) > bed:
            notes.append(
                f"Warning: the tray is {fx:.0f} x {fy:.0f} mm, larger than your {bed:.0f} mm bed. "
                "Shorten it, or rotate it 45 degrees on the plate in Bambu Studio."
            )
        notes.append(
            "Hang it with 4 zip ties (or cord) through the corner slots: back slots tied up near "
            "the bottom of the net, front slots tied a little lower so the tray slopes toward you."
        )
        notes.append("Bambu Studio: print as-is, floor down, no supports. PLA or PETG.")
        return BuildResult([part], print_parts, notes)
