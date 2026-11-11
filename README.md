# 3D Model Builder

A desktop app that turns a few measurements into a print-ready **.3mf** file
for Bambu Studio (also works in OrcaSlicer, PrusaSlicer and Cura).

Pick a template, type your dimensions, check the 3D preview, click **Export .3mf**.

## Template: Curved ball return (store style)

This one is styled after store-bought hoop returns. By default a printed hanger caps the
block where the rim joins the backboard, and the catch ring hangs from it. Set `mount=0` to
hang the ring from the rim on 4 cords instead. The ball drops through the net into the ring, rolls down a curved trough with
windows, and comes back out toward you. It's sized for an 80 mm mini airless ball by default.

| Part | Qty | How it prints |
|------|-----|---------------|
| Chute half: one side of a curved U-channel (70° bend by default): a flat side panel with windows, half of the slotted floor, joining ears, and a rounded spout | 2 (identical) | Flat on its side panel, about 47 mm tall. No supports |
| Swivel ring: an inner ring (the chute ties to it) nested in an outer ring (it hangs from the cords), clicking into 8 directions | 1 (print-in-place) | Flat, as one part. Twist once after printing to free it |
| Hanger: a cap over the rim block, legs down the backboard, and a shelf for the ring | 1 | Lying on its backboard side. No supports |
| Hooks (only with `mount=0`): J-hooks for the rim tube with an eyelet for cord | 4 | Flat |

The full set (2 chute halves, swivel ring, hanger) uses about 99 cm³ of plastic, about 120 g of PLA.

### Printing without supports

The chute is split down the middle of its floor into two identical halves.
- Each half lies flat on its side panel, so the whole panel is the first layer. That's a large, stable footprint.
- The half floor rises from the panel as a short vertical wall, about 47 mm tall.
- The side windows are holes in a flat plate, so they need no bridging.
- The floor slots bridge 10 mm. The joining ears have 45° undersides.
- `test_prints_without_supports` scans every part for overhangs.

**Joining the halves:** put them together floor to floor. Five ears along the back pair
up. Fasten each pair with an M3 × 20 mm screw and nut, or a small zip tie.

With an 80 mm ball the parts need two 256 mm plates. The file lays them out side by side.
In Bambu Studio, add a plate and press **A** (Arrange).

**Chute to ring:** the chute's top end sits flat against the underside of the inner ring.
Four small zip ties lock it on: two through the back wall and one through each side panel. Each tie goes
down through a ring hole, through the slot in the chute wall, and back up through the ring
hole on the other side of the wall.

**Aiming:** the inner ring turns inside the outer ring on a 45° ridge-and-groove joint.
To change direction, lift the chute about 1 mm, turn it, and let it settle into the next
click. There are 8 positions, 45° apart.

**Backboard hanger:** measure the block where the rim meets the backboard. The defaults are
2.25″ wide, 1″ deep and 0.5″ tall. Also measure from the backboard to the centre of the rim.
The cap is a snug fit with 0.4 mm of clearance. Press it down over the block. The ring's
back tab screws up under the hanger's shelf with 2 M3 × 12 mm screws and nuts.

**Rim hooks (`mount=0`):** Tie four 20–30 cm cords from the ring to the hook eyelets. Hang the
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
