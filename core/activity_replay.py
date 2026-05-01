from pathlib import Path
from typing import Any

from core.activity_logger import ActivityLogger


class ActivityReplay:
    """Safe replay helper for non-destructive commands."""

    SAFE_TO_REPLAY = {
        "web_search",
        "weather_report",
        "browser_control",
        "file_intelligence_agent",
        "system_monitor_agent",
    }

    def __init__(self, base_dir: Path):
        self._logger = ActivityLogger(base_dir)

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._logger.list_recent(limit=limit)

    def suggest_replay(self, limit: int = 20) -> str:
        rows = self.recent(limit=limit)
        if not rows:
            return "No activity found for replay."

        lines = ["Recent actions:"]
        for i, row in enumerate(rows, start=1):
            lines.append(
                f"{i}. {row.get('timestamp')} | {row.get('tool')} | "
                f"{row.get('action')} | {row.get('status')}"
            )
        lines.append("Only non-destructive actions are replay-safe without reconfirmation.")
        return "\n".join(lines)

    def get_last_safe_replayable(self, limit: int = 200) -> dict[str, Any] | None:
        rows = self.recent(limit=limit)
        for row in reversed(rows):
            if row.get("status") != "started":
                continue
            tool = str(row.get("tool", "")).strip()
            if tool not in self.SAFE_TO_REPLAY:
                continue
            details = row.get("details", {}) or {}
            args = details.get("args", {}) or {}
            if not isinstance(args, dict):
                args = {}
            return {"tool": tool, "args": args, "action": row.get("action", "")}
        return None
