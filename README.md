# 3D Model Builder

A desktop app that turns a few measurements into a print-ready **.3mf** file
for Bambu Studio (also works in OrcaSlicer, PrusaSlicer and Cura).

Pick a template, type your dimensions, check the 3D preview, click **Export .3mf**.

## Template: Curved ball return (store style)

This one is styled after store-bought hoop returns. A printed hanger caps the block where
the rim joins the backboard and runs down the board. At the bottom, a short block with support
triangles holds the top of a curved chute 20 mm off the board. The ball drops out of the net
onto the chute's curve and comes back out toward you. It's sized for an 80 mm mini airless
ball by default.

| Part | Qty | How it prints |
|------|-----|---------------|
| Chute half: one side of a curved U-channel (65° bend, 35 mm rounded spout): a flat side panel with windows, half of the slotted floor, and joining ears | 2 (identical) | Flat on its side panel, about 47 mm tall. No supports |
| Hanger: a cap over the rim block, a spine down the backboard, and a short screw block with support triangles | 1 | Lying on its backboard side. No supports |

All three parts fit on one 256 mm Bambu plate and use about 94 cm³ of plastic, about 117 g
of PLA.

**The curve sizes itself:** leave "Bend radius" at 0 (automatic). The app then picks the
smallest curve that still has floor under the ball where it drops (the rim centre).
- **With the defaults:** the curve is 120 mm, and the spout reaches 125 mm from the backboard.
- **If the chute is closer to the board, or the rim centre is further out:** the curve has
  to be bigger.
- **Warnings:** the app warns if the ball could miss the chute, or if the spout would stick
  out past the front of the rim.

### Printing without supports

- **Chute:** it's split down the middle of its floor into two identical halves.
  - Each half lies flat on its side panel, so the whole panel is the first layer.
  - The floor slots bridge 10 mm, and the joining ears have 45° undersides.
- **Hanger:** it lies on the side that faces the backboard.
  - The screw block and support triangles rise straight up from the plate.
  - Its two lightening pockets have 10 mm roofs.
- **Check:** `test_prints_without_supports` scans every part for overhangs.

### Assembly

1. **Join the halves:** put them together floor to floor. Six ears along the back pair up.
   Fasten each pair with an M3 × 20 mm screw and nut, or a small zip tie.
2. **Hang it:** press the hanger's cap down over the block where the rim meets the backboard.
   The cap is a snug fit with 0.4 mm of clearance.
3. **Screw on the chute:** fix the top of the chute to the hanger's block with 4 M3 × 16 mm
   screws, 2 per half. Drive them from inside the chute so they thread straight into the
   block's 2.7 mm pilot holes. No nuts are needed.

**Measure first:**
- **The block:** the defaults are 2.25″ wide, 1″ deep and 0.5″ tall.
- **Backboard to rim centre:** this sets where the ball drops and how big the curve gets.
- **Rim inside diameter:** used for the spout check.
- **Block to chute drop:** this must be longer than the net.

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
python -m modelbuilder --cli -o ball_return.3mf --set ball_diameter=80 drop=180
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
