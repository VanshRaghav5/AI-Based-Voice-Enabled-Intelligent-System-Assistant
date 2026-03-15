from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests

from desktop.services.session_store import SessionStore


@dataclass(frozen=True)
class ApiResult:
    ok: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ApiClient:
    def __init__(self, base_url: str, session: SessionStore):
        self.base_url = base_url.rstrip("/")
        self.session = session

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[str], Optional[Dict[str, Any]]]:
        try:
            resp = requests.post(
                self._url("/api/auth/login"),
                json={"username": username, "password": password},
                timeout=10,
            )
            payload = resp.json()
            if resp.status_code == 200 and payload.get("status") == "success":
                token = payload.get("token")
                user = payload.get("user")
                if token and isinstance(user, dict):
                    self.session.save(token, user)
                return True, payload.get("message", "Login successful"), token, user
            return False, payload.get("message", "Login failed"), None, None
        except Exception as exc:
            return False, f"Connection error: {exc}", None, None

    def verify_token(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        try:
            resp = requests.get(self._url("/api/auth/verify"), headers=self.session.auth_headers(), timeout=5)
            if resp.status_code == 200:
                payload = resp.json()
                return True, payload.get("user")
            self.session.clear()
            return False, None
        except Exception:
            return False, None

    def logout(self) -> Tuple[bool, str]:
        try:
            requests.post(self._url("/api/auth/logout"), headers=self.session.auth_headers(), timeout=5)
        except Exception:
            pass
        self.session.clear()
        return True, "Logged out"

    def get_settings(self) -> Tuple[bool, Dict[str, Any]]:
        try:
            resp = requests.get(self._url("/api/settings"), headers=self.session.auth_headers(), timeout=10)
            if resp.status_code == 200:
                return True, resp.json()
            return False, {}
        except Exception:
            return False, {}

    def update_settings(self, settings: Dict[str, Any]) -> ApiResult:
        try:
            resp = requests.post(
                self._url("/api/settings"),
                json=settings,
                headers=self.session.auth_headers(),
                timeout=10,
            )
            payload = resp.json() if resp.content else {}
            ok = resp.status_code in (200, 204) and payload.get("status", "success") != "error"
            return ApiResult(ok=ok, message=payload.get("message", ""), data=payload)
        except Exception as exc:
            return ApiResult(ok=False, message=str(exc), data=None)

    def get_status(self) -> Tuple[bool, Dict[str, Any]]:
        try:
            resp = requests.get(self._url("/api/status"), headers=self.session.auth_headers(), timeout=10)
            if resp.status_code == 200:
                return True, resp.json()
            return False, {}
        except Exception:
            return False, {}

    def health(self) -> Tuple[bool, Dict[str, Any]]:
        try:
            resp = requests.get(self._url("/api/health"), timeout=5)
            if resp.status_code == 200:
                return True, resp.json()
            return False, {}
        except Exception:
            return False, {}

    def process_command(self, command: str, language: Optional[str] = None) -> requests.Response:
        payload: Dict[str, Any] = {"command": command}
        if language:
            payload["language"] = language
        return requests.post(
            self._url("/api/process_command"),
            json=payload,
            headers=self.session.auth_headers(),
            timeout=120,
        )

    def start_listening(self) -> bool:
        try:
            resp = requests.post(self._url("/api/start_listening"), headers=self.session.auth_headers(), timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def stop_listening(self) -> bool:
        try:
            resp = requests.post(self._url("/api/stop_listening"), headers=self.session.auth_headers(), timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def send_confirmation(self, approved: bool) -> ApiResult:
        try:
            resp = requests.post(
                self._url("/api/confirm"),
                json={"approved": approved},
                headers=self.session.auth_headers(),
                timeout=10,
            )
            payload = resp.json() if resp.content else {}
            ok = resp.status_code == 200 and payload.get("status", "success") != "error"
            return ApiResult(ok=ok, message=payload.get("message", ""), data=payload)
        except Exception as exc:
            return ApiResult(ok=False, message=str(exc), data=None)

    def wake_word_status(self) -> Tuple[bool, Dict[str, Any]]:
        try:
            resp = requests.get(self._url("/api/wake_word/status"), headers=self.session.auth_headers(), timeout=10)
            if resp.status_code == 200:
                return True, resp.json()
            return False, {}
        except Exception:
            return False, {}

    def wake_word_start(self) -> bool:
        try:
            resp = requests.post(self._url("/api/wake_word/start"), headers=self.session.auth_headers(), timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def wake_word_stop(self) -> bool:
        try:
            resp = requests.post(self._url("/api/wake_word/stop"), headers=self.session.auth_headers(), timeout=10)
            return resp.status_code == 200
        except Exception:
            return False
