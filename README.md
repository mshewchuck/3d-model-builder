# 3D Model Builder

A desktop app that turns a few measurements into a print-ready **.3mf** file
for Bambu Studio (also works in OrcaSlicer, PrusaSlicer and Cura).

Pick a template, type your dimensions, check the 3D preview, click **Export .3mf**.

## Template: Mini hoop ball return

One flat tray: a thin floor with low side rails and a back stop. It hangs under
the net with zip ties and rolls the ball back to you.

- **One part.** It prints floor-down with **no supports** and no bolts. The default settings are sized for a mini airless ball about the size of a tennis ball (67 mm).
- **Floor cutouts** are slots that run the same way the ball rolls, so it rides on the ribs. They save about a quarter of the plastic and can be turned off.
- **Four zip-tie slots** sit in the corners. Tie the back slots up near the bottom of the net and the front slots a little lower, so the tray slopes toward you.

### What to measure

| Setting | How to measure |
|---------|----------------|
| Ball diameter | Defaults to 67 mm (tennis-ball size). Measure yours |
| Tray length | Keep it under your bed size |
| Printer bed size | 256 for X1/P1/P2, 180 for the A1 mini |

## Running it

```bash
pip install -r requirements.txt
python run_app.py            # desktop app
```

On Linux you may need Tk: `sudo apt install python3-tk`.

Command-line use (no window):

```bash
python -m modelbuilder --cli --list
python -m modelbuilder --cli -o ball_return.3mf --set ball_diameter=127 length=180
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
