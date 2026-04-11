"""Persistent JSON-backed long-term memory."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class LongTermMemory:
    """Durable memory for preferences, habits, and reusable context."""

    def __init__(self, file_path: str = "memory.json") -> None:
        self.file_path = file_path
        self._path = Path(file_path).expanduser().resolve()
        self.data: Dict[str, Any] = self.load()

    def load(self) -> Dict[str, Any]:
        try:
            if not self._path.exists():
                return {}
            with self._path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2, ensure_ascii=True)

    def set(self, key: str, value: Any) -> None:
        self.data[str(key)] = value
        self.save()

    def get(self, key: str):
        return self.data.get(str(key))

    def delete(self, key: str) -> bool:
        normalized = str(key)
        if normalized in self.data:
            del self.data[normalized]
            self.save()
            return True
        return False

    def get_all(self) -> Dict[str, Any]:
        return dict(self.data)
