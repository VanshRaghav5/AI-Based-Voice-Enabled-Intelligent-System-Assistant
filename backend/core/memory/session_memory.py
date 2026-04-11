"""Short-term in-memory session storage."""
from __future__ import annotations

from typing import Any, Dict


class SessionMemory:
    """Volatile memory for current assistant session context."""

    def __init__(self) -> None:
        self.data: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self.data[str(key)] = value

    def get(self, key: str):
        return self.data.get(str(key))

    def delete(self, key: str) -> bool:
        normalized = str(key)
        if normalized in self.data:
            del self.data[normalized]
            return True
        return False

    def get_all(self) -> Dict[str, Any]:
        return dict(self.data)
