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
| Chute: a curved U-channel (65° bend, 35 mm rounded spout) with a slotted floor and flat side panels with windows. The sides slope from 48 mm deep at the top to 34 mm at the spout, with a 45° inward lip along their open edges. A slim glue bead runs along the back seam | 1, which you cut into 2 identical halves in the slicer | Exported lying on a side panel, 94 mm tall. Cut it flat at Z = 47 mm, so each half lies on its side panel. No supports |
| Hanger: a cap over the rim block, a spine down the backboard, and a short screw block with support triangles | 1 | Lying on its backboard side. No supports |

Everything fits on one 256 mm plate, or on two plates on an A1 mini. It uses about 92 cm³
of plastic, about 108 g of PLA.

**The curve sizes itself:** leave "Bend radius" at 0 (automatic). The app then picks the
smallest curve that still has floor under the ball where it drops (the rim centre).
- **With the defaults:** the curve is 120 mm, and the spout reaches 125 mm from the backboard.
- **If the chute is closer to the board, or the rim centre is further out:** the curve has
  to be bigger.
- **Warnings:** the app warns if the ball could miss the chute, or if the spout would stick
  out past the front of the rim.

### Printing without supports

**Splitting the chute in Bambu Studio:** select the chute, open the **Cut** tool, and set a
flat cut at **Z = 47 mm**. That's exactly half its height, along the middle of the floor.
Turn on the option to flip the upper part so it lies on its side panel. You get two
identical halves.

- **Chute:** after the cut, you have two identical halves.
  - Each half lies flat on its side panel, so the whole panel is the first layer.
  - The floor slots bridge 10 mm, and the glue bead has a 45° underside.
  - The edge lips lean at 45°, inward and forward. An outward flare would point down into
    the plate, so it can't print this way.
- **Hanger:** it lies on the side that faces the backboard.
  - The screw block and support triangles rise straight up from the plate.
  - Its two lightening pockets have 10 mm roofs.
- **Check:** `test_prints_without_supports` scans every part for overhangs.

### Assembly

1. **Join the halves:** push three short pieces of 1.75 mm filament, about 6 mm long, into
   the pin holes along the seam. Then glue the halves floor to floor: CA (super) glue for
   PLA, or a plastic cement for PETG. Put glue along the floor edge and the slim bead on the
   back. The hanger's screws also clamp both halves together at the top.
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
