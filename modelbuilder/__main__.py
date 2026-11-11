import sys


def main() -> int:
    if "--cli" in sys.argv:
        from .cli import main as cli_main

        return cli_main([a for a in sys.argv[1:] if a != "--cli"])
    from .gui import main as gui_main

    return gui_main()


if __name__ == "__main__":
    sys.exit(main())
