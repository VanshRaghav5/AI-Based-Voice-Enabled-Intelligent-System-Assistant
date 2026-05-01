import hashlib
import json
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class ConfirmationRequest:
    token: str
    actor: str
    tool: str
    action: str
    risk: str
    params_hash: str
    expires_at: float


class SafetyLayer:
    """Risk scoring + explicit confirmation gate for sensitive actions."""

    RISK_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    CONFIRM_THRESHOLD = "high"

    def __init__(self, ttl_seconds: int = 120):
        self._ttl_seconds = ttl_seconds
        self._pending: dict[str, ConfirmationRequest] = {}
        self._lock = threading.Lock()

    def score_risk(self, tool: str, action: str, params: dict[str, Any]) -> str:
        action_l = (action or "").lower().strip()
        tool_l = (tool or "").lower().strip()

        if tool_l == "system_control_agent":
            if action_l in {"shutdown", "restart", "sleep", "kill_process", "shutdown_in", "restart_in"}:
                return "critical"
            if action_l in {"lock", "list_processes"}:
                return "medium"

        if tool_l in {"file_controller", "file_intelligence_agent"}:
            if action_l in {"delete", "clean_temp_cache"}:
                return "high"
            if action_l in {"find_duplicates", "find_large_files"}:
                return "medium"

        if tool_l in {"send_message", "app_automation_agent"}:
            if action_l in {"send", "send_message", "send_whatsapp"}:
                return "high"

        return "low"

    @staticmethod
    def _stable_hash(params: dict[str, Any]) -> str:
        try:
            packed = json.dumps(params, sort_keys=True, ensure_ascii=True)
        except Exception:
            packed = str(params)
        return hashlib.sha256(packed.encode("utf-8")).hexdigest()[:18]

    def requires_confirmation(self, risk: str) -> bool:
        return self.RISK_ORDER.get(risk, 1) >= self.RISK_ORDER[self.CONFIRM_THRESHOLD]

    def issue_confirmation(self, actor: str, tool: str, action: str, params: dict[str, Any]) -> ConfirmationRequest:
        req = ConfirmationRequest(
            token=uuid.uuid4().hex[:10],
            actor=actor,
            tool=tool,
            action=action,
            risk=self.score_risk(tool, action, params),
            params_hash=self._stable_hash(params),
            expires_at=time.time() + self._ttl_seconds,
        )
        with self._lock:
            self._pending[req.token] = req
        return req

    def validate_confirmation(
        self,
        *,
        token: str,
        actor: str,
        tool: str,
        action: str,
        params: dict[str, Any],
    ) -> tuple[bool, str]:
        with self._lock:
            req = self._pending.get(token)
            if not req:
                return False, "Invalid or expired confirmation token."
            if req.expires_at < time.time():
                del self._pending[token]
                return False, "Confirmation token expired."
            if req.actor != actor:
                return False, "Confirmation token owner mismatch."
            if req.tool != tool or req.action != action:
                return False, "Confirmation token does not match requested action."
            if req.params_hash != self._stable_hash(params):
                return False, "Confirmation token does not match request parameters."
            del self._pending[token]
        return True, "Confirmed"


_GLOBAL_SAFETY: SafetyLayer | None = None


def get_safety_layer() -> SafetyLayer:
    global _GLOBAL_SAFETY
    if _GLOBAL_SAFETY is None:
        _GLOBAL_SAFETY = SafetyLayer()
    return _GLOBAL_SAFETY
