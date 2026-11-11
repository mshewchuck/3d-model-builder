# 3D Model Builder

A desktop app that turns a few measurements into a print-ready **.3mf** file
for Bambu Studio (also works in OrcaSlicer, PrusaSlicer and Cura).

Pick a template, type your dimensions, check the 3D preview, click **Export .3mf**.

## Template: Curved ball return (store style)

This one is styled after store-bought hoop returns. A catch ring hangs from the rim on
4 cords. The ball drops through the net into the ring, rolls down a curved trough with
windows, and comes back out toward you. It's sized for an 80 mm mini airless ball by default.

| Part | Qty | How it prints |
|------|-----|---------------|
| Chute: a curved trough (70° bend by default) with a flat floor, 45° lips, and slots in the floor and lips | 1 | Lying on its side. No supports, Brim set to Outer only |
| Ring: a flat catch collar with cord holes and zip-tie holes | 1 | Flat |
| Hooks: J-hooks for the rim tube with an eyelet for cord | 4 | Flat |

All six parts fit on one 256 mm Bambu plate and use about 84 cm³ of plastic.

### Printing without supports

Print the chute lying on its side, with the curve flat on the plate and the edge of one
lip touching the plate.
- The floor is a vertical wall and the two lips lean at 45°, which is within the range a
  printer handles on its own.
- The floor and lip slots are cut across the chute's path, so their tops bridge 10 mm at
  most. The zip-tie holes bridge 4 mm.
- A test (`test_prints_without_supports`) scans the mesh and fails if any surface
  overhangs past 45° over a longer span.
- Only the thin lip edge touches the plate, so set **Brim** to *Outer only* (about 5 mm)
  in Bambu Studio for grip. Turn supports **off**.

**Assembly:** set the ring on top of the chute and fasten it with 3 small zip ties through
the matching holes. Tie four 20–30 cm cords from the ring to the hook eyelets. Hang the
hooks on the rim so the ring sits just under the net.

## Template: Simple flat tray

The lighter alternative is one flat tray: a thin floor with low side rails and a back stop.
It hangs under the net with 4 zip ties and prints floor-down with no supports.

## Running it

```bash
pip install -r requirements.txt
python run_app.py            # desktop app
```

On Linux you may need Tk: `sudo apt install python3-tk`.

Command-line use (no window):

```bash
python -m modelbuilder --cli --list
python -m modelbuilder --cli -o ball_return.3mf --set ball_diameter=80 ring_opening=110
```

### Prebuilt app

Every push runs `.github/workflows/build.yml`, which builds a standalone
Windows `.exe` and a macOS app. Download them from the **Actions** tab → latest run → *Artifacts*.

## Adding templates

Create a `Template` subclass in `modelbuilder/templates/` with a `params` list
and a `build()` method that returns `BuildResult(assembled=[...], print_parts=[...])`.
Then add it to `TEMPLATES` in `modelbuilder/templates/__init__.py`. Shapes are built
with [manifold3d](https://github.com/elalish/manifold), which always produces
watertight meshes for slicers.

## Tests

```bash
pip install pytest && pytest -q
```
