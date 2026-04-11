"""Unified memory manager used by planning and execution."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from backend.core.memory.long_term_memory import LongTermMemory
from backend.core.memory.session_memory import SessionMemory


class MemoryManager:
    """Coordinates session and persistent memory with context helpers."""

    def __init__(self, long_term_file_path: str | None = None) -> None:
        default_file = Path(__file__).resolve().parents[2] / "data" / "memory.json"
        self.session = SessionMemory()
        self.long_term = LongTermMemory(long_term_file_path or str(default_file))

    def set(self, key: str, value: Any, persistent: bool = False) -> None:
        if persistent:
            self.long_term.set(key, value)
        else:
            self.session.set(key, value)

    def get(self, key: str):
        session_value = self.session.get(key)
        if session_value is not None:
            return session_value
        return self.long_term.get(key)

    def delete(self, key: str, persistent: bool = False) -> bool:
        if persistent:
            return self.long_term.delete(key)
        return self.session.delete(key)

    def get_context(self) -> Dict[str, Dict[str, Any]]:
        return {
            "session": self.session.get_all(),
            "long_term": self.long_term.get_all(),
        }
