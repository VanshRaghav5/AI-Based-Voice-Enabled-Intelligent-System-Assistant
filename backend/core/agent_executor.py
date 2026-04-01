from __future__ import annotations

from typing import Callable

from backend.config.logger import logger
from backend.core.multi_executor import MultiExecutor


class AgentExecutor:
    """Execute tool plans with bounded replanning attempts."""

    def __init__(self, registry, max_agent_iterations: int = 3):
        self.registry = registry
        self.max_agent_iterations = max(1, int(max_agent_iterations))
        self.multi_executor = MultiExecutor(registry)

    def execute_with_replan(self, planner: Callable[[int, list, dict | None], dict]):
        """Run planner/executor loop and return diagnostic summary."""
        loop_trace = []
        loop_history = []
        last_result = None
        last_plan = None

        for iteration in range(1, self.max_agent_iterations + 1):
            try:
                plan = planner(iteration, loop_history, last_result)
            except Exception as exc:
                logger.error(f"[AgentExecutor] Planner error at iteration {iteration}: {exc}")
                last_result = {"status": "error", "message": str(exc), "data": {}}
                loop_history.append(last_result)
                loop_trace.append(
                    {
                        "iteration": iteration,
                        "status": "planner_error",
                        "message": str(exc),
                    }
                )
                break

            if not isinstance(plan, dict):
                last_plan = {"steps": []}
                last_result = {
                    "status": "error",
                    "message": "Planner returned invalid plan format",
                    "data": {},
                }
                loop_history.append(last_result)
                loop_trace.append(
                    {
                        "iteration": iteration,
                        "status": "invalid_plan",
                        "message": "Planner returned non-dict plan",
                    }
                )
                if iteration >= self.max_agent_iterations:
                    break
                continue

            steps = plan.get("steps", [])
            if not isinstance(steps, list):
                plan = dict(plan)
                plan["steps"] = []

            last_plan = plan
            step_count = len(last_plan.get("steps", []))

            # Conversational responses can use chat_reply without any tool steps.
            if step_count == 0:
                last_result = {
                    "status": "success" if str(last_plan.get("chat_reply", "")).strip() else "error",
                    "message": str(last_plan.get("chat_reply", "")).strip() or "Plan contained no executable steps",
                    "data": {"mode": "chat"} if str(last_plan.get("chat_reply", "")).strip() else {},
                }
                loop_history.append(last_result)
                loop_trace.append(
                    {
                        "iteration": iteration,
                        "status": "no_steps",
                        "step_count": 0,
                    }
                )
                break

            results = self.multi_executor.execute(last_plan)
            if isinstance(results, list) and results:
                loop_history.extend(results)
                last_result = results[-1]
            else:
                last_result = {
                    "status": "error",
                    "message": "No execution result returned",
                    "data": {},
                }
                loop_history.append(last_result)

            result_status = str((last_result or {}).get("status", "")).lower()
            loop_trace.append(
                {
                    "iteration": iteration,
                    "status": result_status or "unknown",
                    "step_count": step_count,
                }
            )

            # Terminal states: successful completion, confirmation gate, or final attempt.
            if result_status in {"success", "confirmation_required"}:
                break
            if iteration >= self.max_agent_iterations:
                break

        return {
            "last_plan": last_plan,
            "last_result": last_result or {},
            "loop_trace": loop_trace,
            "loop_history": loop_history,
        }
