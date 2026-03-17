import sys
from pathlib import Path

# Allow running as a script: `python .\desktop\main.py`
# (when executed this way, Python puts the desktop/ folder on sys.path, not the project root)
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from desktop.app import run


if __name__ == "__main__":
    raise SystemExit(run())
