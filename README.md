# 3D Model Builder

A desktop app that turns a few measurements into a print-ready **.3mf** file
for Bambu Studio (also works in OrcaSlicer, PrusaSlicer and Cura).

Pick a template, type your dimensions, check the 3D preview, click **Export .3mf**.

## Template: Mini hoop ball return

A chute that hangs under a mini basketball hoop's net and rolls the ball back to you.

| Part | Qty | How it prints |
|------|-----|---------------|
| Chute (half-pipe with a closed back and two mounting fins) | 1 | Stands on its closed end. Turn on supports (tree, build plate only) for the fins |
| Hanger (snaps onto the rim tube) | 2 | Flat, no supports |

**Hardware:** 4× M4 × 20 mm bolts and nuts.

### What to measure

| Setting | How to measure |
|---------|----------------|
| Ball diameter | Mini balls are usually 5″ (127 mm) or 7″ (178 mm) |
| Rim inside diameter | Across the inside of the rim |
| Rim tube diameter | Thickness of the rim's metal tube. Use calipers if you can |
| Rim to chute height | Must be longer than the net so the ball drops through first |
| Printer bed size | 256 for X1/P1/P2, 180 for the A1 mini |

Tip: print one hanger first to check the clip fits your rim before printing the chute.
PETG is a good material choice because it flexes a little for the snap clip.

## Running it

```bash
pip install -r requirements.txt
python run_app.py            # desktop app
```

On Linux you may need Tk: `sudo apt install python3-tk`.

Command-line use (no window):

```bash
python -m modelbuilder --cli --list
python -m modelbuilder --cli -o ball_return.3mf --set ball_diameter=127 rim_drop=180
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
