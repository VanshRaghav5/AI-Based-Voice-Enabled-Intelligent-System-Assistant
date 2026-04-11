"""Reflection utilities for execution outcomes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ReflectionOutcome:
    retry: bool
    reason: str
    suggestion: str
    should_replan: bool
    memory_updates: List[Dict[str, str]]
    next_steps: List[Dict[str, Any]]


class ReflectionEngine:
    """Analyze execution results and produce retry/replan guidance."""

    def analyze(self, execution_result: Dict[str, Any], plan: Any = None, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = context or {}
        success = bool(execution_result.get("success")) or execution_result.get("status") == "success"
        status = str(execution_result.get("status") or "").lower()
        error = str(execution_result.get("error") or execution_result.get("message") or "").strip()

        if success:
            summary = execution_result.get("message") or "Execution completed successfully."
            return {
                "retry": False,
                "reason": "Execution succeeded",
                "suggestion": summary,
                "should_replan": False,
                "summary": summary,
                "memory_updates": [
                    {"key": "last_execution_status", "value": "success"},
                ],
                "next_steps": [],
                "issues": [],
            }

        suggestion = "Try an alternative command or adjust the parameters."
        lower_error = error.lower()
        next_steps: List[Dict[str, Any]] = []

        if "port" in lower_error and "busy" in lower_error:
            suggestion = "Try a different port or stop the process currently using the port."
            next_steps = [{"action": "run_command", "params": {"command": "python -m http.server 8081"}}]
        elif "permission" in lower_error or "access denied" in lower_error:
            suggestion = "Retry with elevated permissions or a path you can access."
        elif "not found" in lower_error:
            suggestion = "Check the path or command name and try again."

        if status == "confirmation_required":
            suggestion = "Wait for user confirmation before continuing."

        memory_updates = [
            {"key": "last_execution_status", "value": "failed"},
        ]
        if error:
            memory_updates.append({"key": "last_execution_error", "value": error})

        outcome = ReflectionOutcome(
            retry=True,
            reason=error or status or "Step failed",
            suggestion=suggestion,
            should_replan=True,
            memory_updates=memory_updates,
            next_steps=next_steps,
        )

        return {
            "retry": outcome.retry,
            "reason": outcome.reason,
            "suggestion": outcome.suggestion,
            "should_replan": outcome.should_replan,
            "summary": outcome.suggestion,
            "memory_updates": outcome.memory_updates,
            "next_steps": outcome.next_steps,
            "issues": [error] if error else [],
        }