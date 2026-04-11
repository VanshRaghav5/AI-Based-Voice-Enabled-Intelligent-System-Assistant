"""Generate natural assistant-style responses from execution outcomes."""
from __future__ import annotations

from typing import Any, Dict, List


class ResponseGenerator:
    """Create human-friendly summaries for completed agent runs."""

    def generate(self, user_input: str, plan: Any, execution_result: Dict[str, Any], reflection: Dict[str, Any] | None = None) -> str:
        reflection = reflection or {}
        success = bool(execution_result.get("success")) or execution_result.get("status") == "success"
        message = str(execution_result.get("message") or "").strip()

        if not success:
            suggestion = str(reflection.get("suggestion") or "").strip()
            if suggestion:
                return f"I could not finish that yet. {suggestion}"

            if message:
                return f"I could not finish that yet. {message}"

            return "I could not finish that request."

        goal = getattr(plan, "goal", None) or (plan.get("goal") if isinstance(plan, dict) else None) or "your request"
        actions = self._summarize_actions(plan)
        if actions:
            return f"I completed {goal.lower()} by {actions}."

        if message:
            return self._polish(message)

        return f"I completed {goal.lower()}."

    def _summarize_actions(self, plan: Any) -> str:
        steps = getattr(plan, "steps", None)
        if steps is None and isinstance(plan, dict):
            steps = plan.get("steps", [])

        if not steps:
            return ""

        actions: List[str] = []
        for step in steps[:3]:
            if isinstance(step, dict):
                action = step.get("action") or step.get("tool") or step.get("name")
            else:
                action = getattr(step, "action", None) or getattr(step, "tool", None) or getattr(step, "name", None)

            if action:
                actions.append(str(action).replace("_", " "))

        if not actions:
            return ""

        if len(actions) == 1:
            return actions[0]

        return ", ".join(actions[:-1]) + f", and {actions[-1]}"

    @staticmethod
    def _polish(message: str) -> str:
        text = str(message or "").strip()
        if not text:
            return ""
        if text[-1] not in ".!?":
            text = f"{text}."
        return text[0].upper() + text[1:]
