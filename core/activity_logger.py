import json
import time
from pathlib import Path
from typing import Any


class ActivityLogger:
    """Structured activity + error logger used by runtime tools and agents."""

    def __init__(self, base_dir: Path):
        self._root = base_dir / "logs" / "activity"
        self._root.mkdir(parents=True, exist_ok=True)

    def _log_path(self) -> Path:
        date = time.strftime("%Y-%m-%d")
        return self._root / f"{date}.jsonl"

    def log(
        self,
        *,
        actor: str,
        action: str,
        tool: str,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "actor": actor,
            "action": action,
            "tool": tool,
            "status": status,
            "details": details or {},
        }
        try:
            with open(self._log_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=True) + "\n")
        except Exception:
            pass

    def list_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        path = self._log_path()
        if not path.exists():
            return []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
            rows = [json.loads(line) for line in lines if line.strip()]
            return rows[-max(1, min(limit, 500)):]
        except Exception:
            return []


def get_activity_logger(base_dir: Path) -> ActivityLogger:
    return ActivityLogger(base_dir)
