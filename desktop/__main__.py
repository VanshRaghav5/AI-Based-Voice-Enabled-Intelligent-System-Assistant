"""Module entrypoint for OmniAssist Desktop V2.

Run from the repository root:
  python -m desktop

This avoids common sys.path issues when executing `desktop/main.py` directly.
"""

from desktop.app import run


def main() -> int:
    return int(run() or 0)


if __name__ == "__main__":
    raise SystemExit(main())
