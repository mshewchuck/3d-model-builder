"""Launcher used by PyInstaller and for double-click running."""

import sys

from modelbuilder.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
