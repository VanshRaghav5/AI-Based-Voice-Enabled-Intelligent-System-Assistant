"""AgentExecutor for handling iterative plan execution with replanning on failure.

This replaces recursive execution strategies with a bounded iterative loop to
prevent RecursionError during agent execution and tool failure handling.
"""
from typing import Callable, List, Dict, Any, Optional
from backend.config.logger import logger
from backend.core.multi_executor import MultiExecutor


class AgentExecutor:
    """Executes generated plans and handles replanning upon tool failure."""

    def __init__(self, registry, max_agent_iterations: int = 3):
        """Initialize the agent executor.

        Args:
            registry: The tool registry to use for executing tools.
            max_agent_iterations: Maximum number of times to replan and retry on failure.
        """
        self.registry = registry
        self.max_agent_iterations = max(1, max_agent_iterations)
        self.multi_executor = MultiExecutor(self.registry)

    def execute_with_replan(self, planner: Callable) -> Dict[str, Any]:
        """Execute a plan iteratively, requesting a new plan if steps fail.

        Args:
            planner: A callable that generates a plan given (iteration, loop_history, _last_result).

        Returns:
            Dict containing the final state:
            - last_plan: The final plan data requested.
            - loop_trace: Diagnostic trace of iterations and results.
            - loop_history: Flat list of all execution step results.
            - last_result: The very last tool execution result.
        """
        loop_trace: List[Dict[str, Any]] = []
        loop_history: List[Dict[str, Any]] = []
        last_plan: Optional[Any] = None
        last_result: Optional[Dict[str, Any]] = None

        for iteration in range(1, self.max_agent_iterations + 1):
            logger.info(f"[AgentExecutor] Starting iteration {iteration}/{self.max_agent_iterations}")

            # 1. Ask planner for a new plan
            try:
                plan_data = planner(iteration=iteration, loop_history=loop_history, _last_result=last_result)
            except Exception as e:
                logger.error(f"[AgentExecutor] Planner failed: {e}", exc_info=True)
                last_result = {
                    "status": "error",
                    "message": f"Planner failed during iteration {iteration}: {str(e)}",
                    "data": {}
                }
                loop_history.append(last_result)
                break

            last_plan = plan_data

            if not plan_data:
                logger.warning("[AgentExecutor] Empty plan received; terminating loop.")
                break

            # 2. Extract steps to see if it's actionable
            steps = []
            if isinstance(plan_data, dict):
                steps = plan_data.get("steps", [])
            elif hasattr(plan_data, "steps"):
                steps = plan_data.steps

            if not steps:
                logger.info("[AgentExecutor] Plan has no actionable steps; terminating loop.")
                break

            # 3. Execute the plan via MultiExecutor
            execution_results = self.multi_executor.execute(plan_data)
            
            # Record trace
            trace_entry = {
                "iteration": iteration,
                "plan": plan_data,
                "results": execution_results
            }
            loop_trace.append(trace_entry)

            if not execution_results:
                logger.warning("[AgentExecutor] Plan executed but returned no results.")
                break

            loop_history.extend(execution_results)
            last_result = execution_results[-1]
            status = str(last_result.get("status", "")).strip().lower()

            # 4. Check whether we need to replan
            if status == "confirmation_required":
                logger.info("[AgentExecutor] Execution requires user confirmation; pausing agent loop.")
                break

            if status == "success":
                logger.info(f"[AgentExecutor] Plan completed successfully on iteration {iteration}.")
                break

            # If it wasn't successful/confirmation_required, it failed. 
            # It will loop back to ask the planner for a new plan unless we hit the limit.
            logger.warning(f"[AgentExecutor] Step failed. Replanning if iterations remain (status: {status}).")

        # Fallback if iterations exhausted but still failing
        if last_result and last_result.get("status", "success") not in {"success", "confirmation_required"}:
            logger.error("[AgentExecutor] Max iterations reached. Re-planning failed to resolve the issue.")

        return {
            "last_plan": last_plan,
            "loop_trace": loop_trace,
            "loop_history": loop_history,
            "last_result": last_result
        }
