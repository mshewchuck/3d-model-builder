# 3D Model Builder

A desktop app that turns a few measurements into a print-ready **.3mf** file
for Bambu Studio (also works in OrcaSlicer, PrusaSlicer and Cura).

Pick a template, type your dimensions, check the 3D preview, click **Export .3mf**.

## Template: Curved ball return (store style)

This one is styled after store-bought hoop returns. A printed hanger caps the block where
the rim joins the backboard and runs down the board. The top of a curved chute bolts to it,
right under the net. The ball drops out of the net, rolls down the chute, and comes back out
toward you. It's sized for an 80 mm mini airless ball by default.

| Part | Qty | How it prints |
|------|-----|---------------|
| Chute half: one side of a curved U-channel (70° bend by default): a flat side panel with windows, half of the slotted floor, joining ears, and a rounded spout | 2 (identical) | Flat on its side panel, about 47 mm tall. No supports |
| Hanger: a cap over the rim block, legs and a spine down the backboard, and a shelf that bolts to the back of the chute | 1 | Lying on its backboard side. No supports |

All three parts fit on one 256 mm Bambu plate and use about 86 cm³ of plastic, about 107 g of PLA.

### Printing without supports

- **Chute:** it's split down the middle of its floor into two identical halves.
  - Each half lies flat on its side panel, so the whole panel is the first layer. That's a large, stable footprint.
  - The half floor rises from the panel as a short vertical wall, about 47 mm tall.
  - The side windows are holes in a flat plate, so they need no bridging.
  - The floor slots bridge 10 mm, and the joining ears have 45° undersides.
- **Hanger:** it lies on the side that faces the backboard. The cap walls, the shelf and its
  45° brace all rise straight from the plate.
- **Check:** `test_prints_without_supports` scans every part for overhangs.

### Assembly

1. **Join the halves:** put them together floor to floor. Five ears along the back pair up.
   Fasten each pair with an M3 × 20 mm screw and nut, or a small zip tie.
2. **Hang it:** press the hanger's cap down over the block where the rim meets the backboard.
   The cap is a snug fit with 0.4 mm of clearance.
3. **Bolt on the chute:** fix the top of the chute to the hanger's plate with 2 M3 × 10 mm
   screws. The heads go on the hanger side, in counterbores, and the nuts go inside the chute.

**Measure first:**
- **The block:** the defaults are 2.25″ wide, 1″ deep and 0.5″ tall.
- **Backboard to rim centre:** this sets where the ball drops.
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
