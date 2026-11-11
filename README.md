# 3D Model Builder

A desktop app that turns a few measurements into a print-ready **.3mf** file
for Bambu Studio (also works in OrcaSlicer, PrusaSlicer and Cura).

Pick a template, type your dimensions, check the 3D preview, click **Export .3mf**.

## Template: Curved ball return (store style)

This one is styled after store-bought hoop returns. A printed hanger caps the block where
the rim joins the backboard and runs down the board as a ladder frame. Two cheeks at the
bottom of the frame clamp the top of a curved chute. The ball drops out of the net, rolls
down the chute, and comes back out toward you. It's sized for an 80 mm mini airless ball by
default.

| Part | Qty | How it prints |
|------|-----|---------------|
| Chute half: one side of a curved U-channel (65° bend, 70 mm radius, 35 mm rounded spout): a flat side panel with windows, half of the slotted floor, and joining ears | 2 (identical) | Flat on its side panel, about 47 mm tall. No supports |
| Hanger: a cap over the rim block, a ladder frame down the backboard, and two cheeks that clamp the chute | 1 | Lying on its backboard side. No supports |

All three parts fit on one 256 mm Bambu plate and use about 98 cm³ of plastic, about 122 g
of PLA. With the defaults the spout reaches 125 mm out from the backboard, well inside the
front of a 150 mm rim. The app warns you if it would stick out past the rim.

### Printing without supports

- **Chute:** it's split down the middle of its floor into two identical halves.
  - Each half lies flat on its side panel, so the whole panel is the first layer.
  - The half floor rises from the panel as a short vertical wall, about 47 mm tall.
  - The side windows are holes in a flat plate, so they need no bridging.
  - The floor slots bridge 10 mm, and the joining ears have 45° undersides.
- **Hanger:** it lies on the side that faces the backboard.
  - The frame is the first layer.
  - The cap walls and both cheeks rise straight up from the plate.
- **Check:** `test_prints_without_supports` scans every part for overhangs.

### Assembly

1. **Join the halves:** put them together floor to floor. Six ears along the back pair up.
   Fasten each pair with an M3 × 20 mm screw and nut, or a small zip tie.
2. **Hang it:** press the hanger's cap down over the block where the rim meets the backboard.
   The cap is a snug fit with 0.4 mm of clearance.
3. **Clamp the chute:** slide the top of the chute between the two cheeks, with 0.3 mm of
   clearance each side. Fasten it with 6 M3 × 8 mm screws and nuts, 3 per side, heads
   outside. The screws take the chute's weight sideways (in shear), which is much stronger
   than pulling straight out. The cheeks also hold the halves together at the top.

**Measure first:**
- **The block:** the defaults are 2.25″ wide, 1″ deep and 0.5″ tall.
- **Backboard to rim centre:** this sets where the ball drops.
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
