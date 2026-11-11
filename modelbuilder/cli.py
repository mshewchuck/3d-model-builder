"""Command-line entry: build a template and write a .3mf without the GUI.

Example:
    python -m modelbuilder --cli -o ball_return.3mf --set ball_diameter=127 rim_drop=180
"""

from __future__ import annotations

import argparse
import sys

from .templates import TEMPLATES
from .threemf import write_3mf


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="modelbuilder --cli")
    ap.add_argument("--template", default=TEMPLATES[0].name, help="template name")
    ap.add_argument("-o", "--output", default="model.3mf")
    ap.add_argument("--set", nargs="*", default=[], metavar="KEY=VALUE")
    ap.add_argument("--preview", metavar="PNG", help="also save an assembled-view preview image")
    ap.add_argument("--list", action="store_true", help="list templates and parameters")
    args = ap.parse_args(argv)

    if args.list:
        for t in TEMPLATES:
            print(t.name)
            for p in t.params:
                print(f"  {p.key:20} {p.default:>7g} {p.unit:4} {p.label}")
        return 0

    by_name = {t.name: t for t in TEMPLATES}
    if args.template not in by_name:
        print(f"Unknown template {args.template!r}", file=sys.stderr)
        return 2
    t = by_name[args.template]
    values = t.defaults()
    for item in args.set:
        key, _, val = item.partition("=")
        if key not in values:
            print(f"Unknown parameter {key!r}", file=sys.stderr)
            return 2
        values[key] = float(val)
    errors = t.validate(values)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2

    result = t.build(values)
    write_3mf(args.output, [p.to_mesh() for p in result.print_parts], title=t.name)
    print(f"Wrote {args.output}")
    if args.preview:
        from .preview import save_preview_png

        save_preview_png(result.assembled, args.preview, t.name)
        print(f"Wrote {args.preview}")
    for n in result.notes:
        print(n)
    return 0
