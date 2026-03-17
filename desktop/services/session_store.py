from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


DEFAULT_TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".omniassist", "token.json")


@dataclass
class SessionInfo:
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

    @property
    def role(self) -> str:
        if not isinstance(self.user, dict):
            return "user"
        return str(self.user.get("role") or "user")


class SessionStore:
    """Stores the current JWT + user metadata on disk for desktop clients."""

    def __init__(self, token_file: str = DEFAULT_TOKEN_FILE):
        self._token_file = token_file
        self._cached = SessionInfo()

    def _ensure_dir(self) -> None:
        os.makedirs(os.path.dirname(self._token_file), exist_ok=True)

    def save(self, token: str, user: Dict[str, Any]) -> None:
        self._cached = SessionInfo(token=token, user=user)
        self._ensure_dir()
        with open(self._token_file, "w", encoding="utf-8") as f:
            json.dump({"token": token, "user": user}, f)

    def load(self) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        if self._cached.token:
            return self._cached.token, self._cached.user

        if os.path.exists(self._token_file):
            try:
                with open(self._token_file, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                self._cached = SessionInfo(token=payload.get("token"), user=payload.get("user"))
            except Exception:
                self._cached = SessionInfo()

        return self._cached.token, self._cached.user

    def clear(self) -> None:
        self._cached = SessionInfo()
        try:
            if os.path.exists(self._token_file):
                os.remove(self._token_file)
        except Exception:
            pass

    def auth_headers(self) -> Dict[str, str]:
        token, _ = self.load()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    @property
    def user(self) -> Optional[Dict[str, Any]]:
        self.load()
        return self._cached.user

    @property
    def token(self) -> Optional[str]:
        self.load()
        return self._cached.token
