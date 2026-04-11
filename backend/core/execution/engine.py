"""Execution engine that converts plans into tool execution with retry logic."""
from __future__ import annotations

from typing import List, Dict, Any
from pathlib import Path
from backend.core.execution.tool_registry import ToolRegistry
from backend.core.memory.memory_manager import MemoryManager
from backend.utils.logger import log


class ExecutionEngine:
    """Execute structured plans using the tool registry with retry and safety logic."""

    def __init__(self, registry: ToolRegistry, max_retries: int = 2, memory: MemoryManager | None = None) -> None:
        """Initialize execution engine.
        
        Args:
            registry: ToolRegistry instance for tool execution.
            max_retries: Maximum retry attempts per step (default: 2).
        """
        self.registry = registry
        self.max_retries = max_retries
        self.memory = memory or MemoryManager()

    def _update_memory_after_execution(self, plan, result: Dict[str, Any]) -> None:
        metadata = getattr(plan, "metadata", {}) or {}
        plan_intent = metadata.get("intent")

        if plan_intent:
            self.memory.set("last_intent", plan_intent)
            # Persist resume intent so it is available after restart.
            self.memory.set("last_intent", plan_intent, persistent=True)
        self.memory.set("last_plan", getattr(plan, "goal", ""))
        self.memory.set("last_plan", getattr(plan, "goal", ""), persistent=True)

        if plan_intent == "start_work_session":
            self.memory.set("last_task", "work_session")

        for item in result.get("results", []):
            action = item.get("action")
            params = item.get("params", {}) if isinstance(item.get("params"), dict) else {}

            if action:
                self.memory.set("last_action", action)
                self.memory.set("last_action", action, persistent=True)

            if action == "open_project":
                project_path = params.get("path")
                if project_path:
                    normalized = str(Path(str(project_path)).expanduser().resolve())
                    self.memory.set("project_path", normalized, persistent=True)
                    self.memory.set("last_project", normalized)
                    self.memory.set("last_project", normalized, persistent=True)

        success = bool(result.get("success"))
        self.memory.set("last_execution_status", "success" if success else "failed")

    def execute_plan(self, plan) -> Dict[str, Any]:
        """Execute a structured plan with safety checks and logging.
        
        Args:
            plan: Plan object with goal and steps.
            
        Returns:
            Dictionary with success status and execution results.
        """
        # Safety check: require confirmation if needed
        if plan.requires_confirmation:
            log(f"Safety Check: Plan requires user confirmation before execution")
            blocked_result = {
                "success": False,
                "error": "User confirmation required",
                "results": []
            }
            self._update_memory_after_execution(plan, blocked_result)
            return blocked_result

        log(f"Engine: Executing plan: {plan.goal}")
        results = []

        for step in plan.steps:
            log(f"Engine: Running step {step.step_id}: [{step.action}]")
            
            # Execute step with retries
            result = self._execute_step(step)
            
            results.append({
                "step": step.step_id,
                "action": step.action,
                "params": step.params,
                "result": result,
            })

            # Fail fast on error
            if not result.get("success"):
                log(f"Engine: Step {step.step_id} failed - {result.get('error')}")
                failed_result = {
                    "success": False,
                    "failed_step": step.step_id,
                    "error": result.get("error"),
                    "results": results
                }
                self._update_memory_after_execution(plan, failed_result)
                return failed_result

        log(f"Engine: Execution successful - {len(results)} steps completed")
        final_result = {
            "success": True,
            "results": results
        }
        self._update_memory_after_execution(plan, final_result)
        return final_result

    def _execute_step(self, step, attempt: int = 0) -> Dict[str, Any]:
        """Execute a single step with retry logic.
        
        Args:
            step: Step object with action and params.
            attempt: Current attempt number.
            
        Returns:
            Execution result from the tool.
        """
        try:
            result = self.registry.execute(step.action, step.params or {})
            
            if result.get("success"):
                log(f"Engine:   [OK] Step {step.step_id} succeeded")
                return result
            
            # Retry on failure
            if attempt < self.max_retries:
                log(f"Engine:   [RETRY] Step {step.step_id} failed, retrying (attempt {attempt + 1}/{self.max_retries})")
                return self._execute_step(step, attempt + 1)
            
            log(f"Engine:   [FAIL] Step {step.step_id} failed after {self.max_retries} retries")
            return result
            
        except Exception as e:
            log(f"Engine:   [ERROR] Step {step.step_id} exception: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception in step {step.step_id}"
            }
