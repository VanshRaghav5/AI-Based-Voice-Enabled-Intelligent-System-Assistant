"""Core planner that converts intent data into structured plans."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import requests

from backend.core.intent.classifier import IntentClassifier
from backend.core.planner.schema import Plan, Step
from backend.core.planner.workflows import (
    continue_work_workflow,
    open_app_workflow,
    open_project_workflow,
    organize_files,
    run_command_workflow,
    search_web_workflow,
    start_work_session,
)
from backend.services.llm_service import LLMClient
from backend.utils.logger import log
from backend.utils.settings import LLM_TIMEOUT_SECONDS


class Planner:
    """Create structured plans from classified intent data."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.classifier = IntentClassifier()
        self._llm_client = llm_client

    @staticmethod
    def _context_lookup(context, key, default=None):
        if not isinstance(context, dict):
            return default

        session = context.get("session", {}) if isinstance(context.get("session"), dict) else {}
        long_term = context.get("long_term", {}) if isinstance(context.get("long_term"), dict) else {}

        if key in session and session.get(key) is not None:
            return session.get(key)
        if key in long_term and long_term.get(key) is not None:
            return long_term.get(key)
        return default

    def _get_llm_client(self) -> LLMClient | None:
        if self._llm_client is None:
            self._llm_client = LLMClient()
        return self._llm_client

    @staticmethod
    def _context_preview(context) -> str:
        if not context:
            return "{}"

        try:
            return json.dumps(context, ensure_ascii=True, default=str)
        except Exception:
            return str(context)

    @staticmethod
    def _normalize_step_payload(step: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(step, dict):
            return None

        action = step.get("action") or step.get("tool") or step.get("name")
        if not action:
            return None

        params = step.get("params")
        if params is None:
            params = step.get("parameters")
        if params is None:
            params = step.get("args")
        if params is None:
            params = step.get("arguments")
        if not isinstance(params, dict):
            params = {}

        return {"action": str(action), "params": params}

    def _normalize_step_collection(self, plan_data: Any) -> List[Dict[str, Any]]:
        if isinstance(plan_data, list):
            raw_steps = plan_data
        elif isinstance(plan_data, dict):
            raw_steps = (
                plan_data.get("steps")
                or plan_data.get("next_steps")
                or plan_data.get("tool_calls")
                or []
            )

            # Some models return numbered objects instead of arrays:
            # {"0": {...}, "1": {...}}. Convert this into an ordered list.
            if not raw_steps:
                numeric_items = []
                for key, value in plan_data.items():
                    if str(key).isdigit() and isinstance(value, dict):
                        numeric_items.append((int(str(key)), value))
                if numeric_items:
                    raw_steps = [value for _, value in sorted(numeric_items, key=lambda item: item[0])]
        else:
            raw_steps = []

        normalized_steps: List[Dict[str, Any]] = []
        for step in raw_steps:
            normalized = self._normalize_step_payload(step)
            if normalized:
                normalized_steps.append(normalized)
        return normalized_steps

    @staticmethod
    def _serialize_plan(plan: Plan | Dict[str, Any] | None) -> Dict[str, Any]:
        if isinstance(plan, Plan):
            return {
                "goal": plan.goal,
                "steps": [
                    {"step_id": step.step_id, "action": step.action, "params": step.params}
                    for step in plan.steps
                ],
                "requires_confirmation": plan.requires_confirmation,
                "metadata": plan.metadata,
            }

        if isinstance(plan, dict):
            return plan

        return {}

    def _build_plan(self, goal: str, steps_data: List[Dict[str, Any]], intent: str, confidence: float, user_input: str, context: dict, planner_mode: str, plan_source: str | None = None) -> Plan:
        steps = []
        for index, step in enumerate(steps_data):
            steps.append(Step(index, step["action"], step.get("params", {})))
            log(f"  Step {index}: {step['action']} {step.get('params', {})}")

        metadata = {
            "intent": intent,
            "confidence": confidence,
            "user_input": user_input,
            "context_used": bool(context),
            "planner_mode": planner_mode,
        }
        if plan_source:
            metadata["plan_source"] = plan_source

        return Plan(goal, steps, False, metadata=metadata)

    def _build_llm_prompt(self, user_input: str, intent: str, context: dict, intent_payload: dict) -> str:
        """Build strong prompt that teaches LLM how to think.
        
        This is the CORE reasoning instruction. Better prompt = better decisions.
        """
        available_tools = [
            "open_app",
            "run_command",
            "open_url",
            "create_file",
            "read_file",
            "write_file",
            "search_files",
            "organize_files",
        ]

        tool_descriptions = """
TOOL REFERENCE:
- open_app: {"params": {"app_name": "code"}} - Opens VS Code, terminal, etc.
- run_command: {"params": {"command": "python script.py"}} - Executes shell command
- open_url: {"params": {"url": "https://example.com"}} - Opens browser
- create_file: {"params": {"path": "/path/file.txt", "content": "..."}} - Creates new file
- read_file: {"params": {"path": "/path/file.txt"}} - Reads file content
- write_file: {"params": {"path": "/path/file.txt", "content": "..."}} - Writes to file
- search_files: {"params": {"query": "pattern", "directory": "/path"}} - Searches files
- organize_files: {"params": {"directory": "/path", "strategy": "by_type"}} - Organizes directory
"""

        examples = """
EXAMPLE 1 - Setup ML project:
User: "Setup my ML project with Python environment"
Thinking: Need Python env, maybe create venv, install deps, open editor
Result:
[
  {"action": "open_app", "params": {"app_name": "terminal"}},
  {"action": "run_command", "params": {"command": "python -m venv ml_env"}},
    {"action": "run_command", "params": {"command": "ml_env\\Scripts\\activate && pip install numpy pandas", "cwd": "E:\\Projects\\ml-app"}},
  {"action": "open_app", "params": {"app_name": "code"}}
]

EXAMPLE 2 - Web search task:
User: "Search for Python async patterns and show me examples"
Thinking: Search web, then read + create examples
Result:
[
  {"action": "open_url", "params": {"url": "https://python-async-docs.example.com"}},
  {"action": "create_file", "params": {"path": "./async_examples.py", "content": "# Async pattern examples..."}}
]
"""

        context_summary = ""
        if context:
            if isinstance(context.get("session"), dict):
                session = context["session"]
                if session.get("last_project"):
                    context_summary += f"\nLast project: {session['last_project']}\n"
                if session.get("current_directory"):
                    context_summary += f"Current directory: {session['current_directory']}\n"

        return f"""You are an AI assistant that breaks complex tasks into executable steps.

Your job: Analyze the user's request and create a PLAN as a JSON array of steps.

{tool_descriptions}

{examples}

USER REQUEST: {user_input}

Detected Intent: {intent}
Intent Payload: {json.dumps(intent_payload or {}, ensure_ascii=True, default=str)}

{context_summary}

INSTRUCTIONS:
1. Break the task into logical steps (2-5 steps typical)
2. Use the tools above - nothing else
3. Return ONLY valid JSON array
4. Each step must have "action" and "params"
5. For run_command steps, include "cwd" when project files are involved
6. Prefer Windows-compatible commands (PowerShell/cmd) instead of Unix shell syntax
7. If path is unknown, use relative paths (e.g., "src/main.py") so executor can resolve to working directory
8. No explanations, no markdown - pure JSON

RESPOND WITH JSON ARRAY ONLY:"""


    def _build_reflection_prompt(self, user_input: str, plan: Plan | Dict[str, Any], execution_result: Dict[str, Any], context: dict) -> str:
        return (
            "You are an AI assistant reflection engine.\n\n"
            f"User request: {user_input}\n\n"
            f"Original plan: {json.dumps(self._serialize_plan(plan), ensure_ascii=True, default=str)}\n\n"
            f"Execution result: {json.dumps(execution_result or {}, ensure_ascii=True, default=str)}\n\n"
            f"Context: {self._context_preview(context)}\n\n"
            "Analyze the run and return JSON with this schema:\n"
            "{\n"
            '  "summary": "...",\n'
            '  "success": true,\n'
            '  "issues": ["..."],\n'
            '  "memory_updates": [{"key": "...", "value": "..."}],\n'
            '  "should_replan": false,\n'
            '  "next_steps": [{"action": "...", "params": {...}}]\n'
            "}"
        )

    def _parse_json_payload(self, text: str) -> Any:
        if not text:
            return None

        candidate = text.strip()
        code_block = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL | re.IGNORECASE)
        if code_block:
            candidate = code_block.group(1).strip()

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            start = min([pos for pos in [candidate.find("{"), candidate.find("[")] if pos != -1], default=-1)
            end = max(candidate.rfind("}"), candidate.rfind("]"))
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(candidate[start : end + 1])
                except json.JSONDecodeError:
                    return None
            return None

    def _invoke_llm_json(self, prompt: str) -> Any:
        llm_client = self._get_llm_client()
        if llm_client is None or not llm_client.ollama_available:
            return None

        try:
            full_prompt = f"{llm_client.system_prompt}\n\n{prompt}\n\nJSON RESPONSE:"
            payload = {
                "model": llm_client.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 512,
                    "top_k": 20,
                    "top_p": 0.9,
                },
            }

            response = llm_client.session.post(
                f"{llm_client.ollama_api_url}/api/generate",
                json=payload,
                timeout=LLM_TIMEOUT_SECONDS,
            )
            if response.status_code != 200:
                log(f"Planner: LLM request failed with status {response.status_code}")
                return None

            output = response.json().get("response", "").strip()
            return self._parse_json_payload(output)
        except requests.RequestException as exc:
            log(f"Planner: LLM request error: {exc}")
        except Exception as exc:
            log(f"Planner: Unexpected LLM error: {exc}")

        return None

    def _create_rule_based_plan(self, intent: str, intent_payload: dict, context: dict, confidence: float, user_input: str) -> Optional[Plan]:
        if intent == "start_work_session":
            steps_data = start_work_session()
            goal = "Start work session"
            log(f"Planner: Building plan for start_work_session with {len(steps_data)} steps")
        elif intent == "organize_files":
            steps_data = organize_files()
            goal = "Organize files"
            log(f"Planner: Building plan for organize_files with {len(steps_data)} steps")
        elif intent == "run_command":
            command = intent_payload.get("command") or user_input
            steps_data = run_command_workflow(command)
            goal = "Run command"
            log(f"Planner: Building plan for run_command with {len(steps_data)} steps")
        elif intent == "open_app":
            app_name = intent_payload.get("app_name") or user_input
            steps_data = open_app_workflow(app_name)
            goal = "Open application"
            log(f"Planner: Building plan for open_app with {len(steps_data)} steps")
        elif intent == "search_web":
            query = intent_payload.get("query") or user_input
            steps_data = search_web_workflow(query)
            goal = "Search web"
            log(f"Planner: Building plan for search_web with {len(steps_data)} steps")
        elif intent == "continue_work":
            last_plan = self._context_lookup(context, "last_plan", "")
            last_intent = self._context_lookup(context, "last_intent", "")
            last_project = (
                self._context_lookup(context, "last_project", "")
                or self._context_lookup(context, "project_path", "")
            )
            steps_data = continue_work_workflow(
                str(last_plan or ""),
                str(last_project or ""),
                str(last_intent or ""),
            )
            goal = "Continue previous work"
            log(
                f"Planner: Building plan for continue_work with {len(steps_data)} steps using last_project='{last_project}' and last_intent='{last_intent}'"
            )
        elif intent == "open_project":
            project_path = (
                intent_payload.get("path")
                or self._context_lookup(context, "project_path", "")
                or self._context_lookup(context, "last_project", "")
            )
            steps_data = open_project_workflow(str(project_path or ""))
            goal = "Open project"
            log(f"Planner: Building plan for open_project with {len(steps_data)} steps")
        else:
            return None

        return self._build_plan(
            goal=goal,
            steps_data=steps_data,
            intent=intent,
            confidence=confidence,
            user_input=user_input,
            context=context,
            planner_mode="rule_based",
        )

    def _create_llm_plan(self, intent: str, intent_payload: dict, user_input: str, context: dict, confidence: float) -> Optional[Plan]:
        """Create plan using LLM reasoning.
        
        THIS IS WHERE LLM ACTUALLY THINKS.
        Prompt teaches LLM the task structure, then LLM generates steps.
        """
        llm_client = self._get_llm_client()
        if llm_client is None or not llm_client.ollama_available:
            log("Planner: LLM not available, cannot create LLM plan")
            return None

        prompt = self._build_llm_prompt(user_input, intent, context, intent_payload)
        
        # CORE: LLM generates the response (string)
        raw_response = llm_client.generate(prompt)
        if not raw_response:
            log("Planner: LLM returned empty response")
            return None

        # Parse JSON from LLM response string
        raw_plan = self._parse_json_payload(raw_response)
        if not raw_plan:
            log(f"Planner: LLM response not valid JSON. Raw: {raw_response[:200]}")
            return None

        # Extract steps from parsed plan
        steps_data = self._normalize_step_collection(raw_plan)
        if not steps_data:
            log(f"Planner: LLM plan has no executable steps. Parsed: {raw_plan}")
            return None

        goal = "LLM-generated task plan"
        
        log(f"✅ LLM PLAN CREATED: {len(steps_data)} steps for '{user_input[:50]}'")
        
        return self._build_plan(
            goal=goal,
            steps_data=steps_data,
            intent=intent,
            confidence=confidence,
            user_input=user_input,
            context=context,
            planner_mode="llm",
            plan_source="ollama",
        )

    def _fallback_unknown_plan(self, intent: str, confidence: float, user_input: str, context: dict) -> Plan:
        plan = Plan(
            "Unknown task",
            [],
            False,
            metadata={
                "intent": intent,
                "confidence": confidence,
                "user_input": user_input,
                "context_used": bool(context),
                "planner_mode": "fallback",
            },
        )
        log("Planner: No matching workflow or LLM steps, using unknown fallback")
        log(f"Plan created: {plan.goal} (0 steps)")
        return plan

    def _fallback_reflection(self, user_input: str, plan: Plan | Dict[str, Any], execution_result: Dict[str, Any], context: dict) -> Dict[str, Any]:
        success = bool(execution_result.get("success")) or execution_result.get("status") == "success"
        error_message = execution_result.get("error") or execution_result.get("message") or ""
        summary = "Execution succeeded."
        if not success:
            summary = f"Execution failed: {error_message}" if error_message else "Execution failed."

        memory_updates = [{"key": "last_execution_status", "value": "success" if success else "failed"}]
        if not success and execution_result.get("failed_step") is not None:
            memory_updates.append({"key": "last_failed_step", "value": str(execution_result.get("failed_step"))})

        return {
            "summary": summary,
            "success": success,
            "issues": [error_message] if error_message and not success else [],
            "memory_updates": memory_updates,
            "should_replan": not success,
            "next_steps": [],
            "source": "fallback",
            "user_input": user_input,
            "plan": self._serialize_plan(plan),
            "context_used": bool(context),
        }

    def _normalize_reflection(self, reflection: Any, user_input: str, plan: Plan | Dict[str, Any], execution_result: Dict[str, Any], context: dict) -> Dict[str, Any]:
        fallback = self._fallback_reflection(user_input, plan, execution_result, context)
        if not isinstance(reflection, dict):
            return fallback

        issues = reflection.get("issues", [])
        if not isinstance(issues, list):
            issues = [str(issues)] if issues else []

        memory_updates = reflection.get("memory_updates", [])
        if not isinstance(memory_updates, list):
            memory_updates = []

        normalized_memory_updates = []
        for item in memory_updates:
            if isinstance(item, dict) and item.get("key") is not None:
                normalized_memory_updates.append({"key": str(item.get("key")), "value": str(item.get("value", ""))})

        next_steps = self._normalize_step_collection(reflection)
        if not next_steps:
            next_steps = fallback["next_steps"]

        summary = reflection.get("summary") or fallback["summary"]
        success = reflection.get("success")
        if not isinstance(success, bool):
            success = fallback["success"]

        should_replan = reflection.get("should_replan")
        if not isinstance(should_replan, bool):
            should_replan = fallback["should_replan"]

        return {
            "summary": str(summary),
            "success": success,
            "issues": issues,
            "memory_updates": normalized_memory_updates or fallback["memory_updates"],
            "should_replan": should_replan,
            "next_steps": next_steps,
            "source": reflection.get("source", "ollama"),
            "user_input": user_input,
            "plan": self._serialize_plan(plan),
            "context_used": bool(context),
        }

    def create_plan(self, intent_data, user_input: str, context=None):
        """Convert intent data into a structured plan."""
        if isinstance(intent_data, str):
            intent_data = {"intent": intent_data}

        intent = (intent_data or {}).get("intent", "unknown")
        confidence = (intent_data or {}).get("confidence", 0.0)
        log(f"Intent detected: {intent} (confidence: {confidence})")

        if intent == "unknown" and user_input:
            upgraded_intent = self.classifier.classify(user_input, use_llm=True)
            if upgraded_intent.get("intent") and upgraded_intent.get("intent") != "unknown":
                intent = upgraded_intent.get("intent", intent)
                confidence = upgraded_intent.get("confidence", confidence)
                intent_data = {**(intent_data or {}), **upgraded_intent}
                log(f"Planner: Upgraded intent via classifier to {intent} (confidence: {confidence})")

        intent_payload = (intent_data or {}).get("data", {})
        if not isinstance(intent_payload, dict):
            intent_payload = {}

        context = context or {}

        rule_plan = self._create_rule_based_plan(intent, intent_payload, context, confidence, user_input)
        if rule_plan is not None:
            log(f"Plan created: {rule_plan.goal} ({len(rule_plan.steps)} steps)")
            return rule_plan

        llm_plan = self._create_llm_plan(intent, intent_payload, user_input, context, confidence)
        if llm_plan is not None:
            log(f"Plan created: {llm_plan.goal} ({len(llm_plan.steps)} steps)")
            return llm_plan

        return self._fallback_unknown_plan(intent, confidence, user_input, context)

    def reflect_on_execution(self, user_input: str, plan: Plan | Dict[str, Any], execution_result: Dict[str, Any], context=None):
        """Reflect on a completed execution and suggest next actions."""
        context = context or {}
        prompt = self._build_reflection_prompt(user_input, plan, execution_result or {}, context)
        reflection = self._invoke_llm_json(prompt)
        normalized = self._normalize_reflection(reflection, user_input, plan, execution_result or {}, context)
        log(f"Planner: Reflection generated (should_replan={normalized['should_replan']})")
        return normalized