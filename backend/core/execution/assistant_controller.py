from backend.services.llm_service import LLMClient
from backend.core.execution.tool_registry import ToolRegistry
from backend.core.execution.executor import Executor
from backend.core.execution.multi_executor import MultiExecutor
from backend.core.execution.reflection import ReflectionEngine
from backend.core.memory.memory_store import MemoryStore
from backend.core.memory.command_processor import MemoryCommandProcessor
from backend.core.planner.planner import Planner
from backend.core.execution.response_generator import ResponseGenerator
from backend.tools.dev_tools import register_all_tools
from backend.utils.logger import logger, log
from backend.utils.assistant_config import assistant_config
from backend.core.execution.persona import persona
from backend.core.execution.response_formatter import ResponseFormatter
from backend.core.execution.translation_service import TranslationService
import json
import os
import re


class AssistantController:

    def __init__(self):
        """Initialize the assistant controller with core components."""
        # Initialize LLM client with configured/default model
        self.llm_client = LLMClient()
        self.planner = Planner(llm_client=self.llm_client)
        
        # Initialize registry and tool executor
        self.registry = ToolRegistry()
        self.executor = Executor(self.registry)
        register_all_tools(self.registry)
        
        # Initialize multi-executor
        self.multi_executor = MultiExecutor(self.registry)
        
        # Initialize session state
        self.memory = MemoryStore()
        self.memory_commands = MemoryCommandProcessor(self.memory)
        self.reflection_engine = ReflectionEngine()
        self.response_generator = ResponseGenerator()

        # Optional translator for multi-language command and response handling
        self.translation = TranslationService()
        self.response_formatter = ResponseFormatter()
        
        # Track pending plan and step for confirmation
        self.pending_plan = None
        self.pending_step_index = 0
        self.pending_confirmation_result = None

        # Agent loop diagnostics for UI and debugging
        self.last_plan_data = None
        self.last_loop_trace = []

        # Bounded loop avoids runaway replanning on persistent tool failures
        self.max_agent_iterations = 3
        
        logger.info("[AssistantController] Initialized successfully")

    def _get_plan_steps(self, plan_data):
        """Return normalized plan steps from dict/object plan formats."""
        if not plan_data:
            return []

        if isinstance(plan_data, dict):
            return plan_data.get("steps", [])

        return getattr(plan_data, "steps", []) if hasattr(plan_data, "steps") else []

    def _infer_active_goal(self, user_text: str) -> str:
        """Infer a compact goal label for long-running tasks."""
        cleaned = (user_text or "").strip().rstrip(".?!")
        lowered = cleaned.lower()

        prefixes = [
            "help me complete ",
            "help me with ",
            "work on ",
            "complete ",
            "finish ",
            "continue ",
            "start ",
            "build ",
            "create ",
        ]
        for prefix in prefixes:
            if lowered.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break

        cleaned = cleaned.lstrip("my ").strip()
        return cleaned or "current task"

    def _build_replan_prompt(self, user_text: str, loop_history: list, iteration: int, reflection_feedback: dict | None = None) -> str:
        """Build a concise prompt for iterative re-planning using prior observations."""
        recent = loop_history[-3:] if loop_history else []
        observation = json.dumps(recent, ensure_ascii=True)
        reflection_block = ""
        if isinstance(reflection_feedback, dict) and reflection_feedback:
            reflection_block = (
                f"\nREFLECTION SUMMARY: {reflection_feedback.get('summary', '')}\n"
                f"REFLECTION ISSUES: {json.dumps(reflection_feedback.get('issues', []), ensure_ascii=True)}\n"
                f"REFLECTION SUGGESTION: {reflection_feedback.get('suggestion', '')}\n"
                f"REFLECTION NEXT STEPS: {json.dumps(reflection_feedback.get('next_steps', []), ensure_ascii=True)}\n"
            )
        return (
            f"{user_text}\n\n"
            f"REPLAN ITERATION: {iteration}\n"
            f"RECENT EXECUTION OBSERVATIONS (JSON): {observation}\n"
            f"{reflection_block}"
            "Generate a corrected plan that avoids failed steps and uses valid tools. "
            "Return strict JSON with a 'steps' array."
        )

    def _build_memory_context(self):
        """Build compact memory context for planning prompts."""
        state = self.memory.get_state()
        facts = getattr(state, "facts", {}) or {}
        facts_preview = list(facts.items())[:5]
        return (
            f"MEMORY CONTEXT:\n"
            f"- last_file_path: {state.last_file_path}\n"
            f"- last_contact: {state.last_contact}\n"
            f"- last_url: {state.last_url}\n"
            f"- saved_facts_preview: {facts_preview}\n"
        )

    def _resolve_working_directory(self) -> str | None:
        """Resolve best-known working directory from memory state."""
        state = self.memory.get_state()
        facts = getattr(state, "facts", {}) or {}

        candidates = [
            facts.get("working_directory"),
            facts.get("project_path"),
            getattr(state, "last_folder_path", None),
        ]

        last_file = getattr(state, "last_file_path", None)
        if last_file:
            try:
                candidates.append(os.path.dirname(str(last_file)))
            except Exception:
                pass

        for candidate in candidates:
            if candidate and os.path.isdir(str(candidate)):
                return str(candidate)
        return None

    def _extract_directory_from_text(self, text: str) -> str | None:
        """Extract Windows directory path from user text when provided explicitly."""
        if not text:
            return None

        matches = re.findall(r"([A-Za-z]:\\[^\n\r\t\"']+)", text)
        for raw in matches:
            candidate = raw.strip().rstrip(".,;)")
            if os.path.isdir(candidate):
                return candidate
        return None

    def _handle_working_directory_command(self, text: str):
        """Capture commands like 'working directory is ...' without running planner/executor."""
        lowered = (text or "").lower()
        if not any(phrase in lowered for phrase in ["working directory", "work directory", "project directory", "set directory"]):
            return None

        directory = self._extract_directory_from_text(text)
        if not directory:
            return {
                "status": "needs_input",
                "message": "Please provide a valid folder path to set as working directory.",
                "data": {"required": "working_directory"},
            }

        self.memory.update({"last_folder_path": directory})
        self.memory.remember_fact("working_directory", directory)
        self.memory.remember_fact("project_path", directory)
        return {
            "status": "success",
            "message": f"Working directory set to {directory}",
            "data": {"working_directory": directory},
        }

    def _plan_to_dict(self, plan_obj):
        """Convert Plan object/dict to executor-friendly dict format."""
        if isinstance(plan_obj, dict):
            return plan_obj

        steps = []
        for step in getattr(plan_obj, "steps", []) or []:
            action = getattr(step, "action", None)
            params = getattr(step, "params", {}) or {}
            if action:
                steps.append({"name": action, "args": params})

        return {
            "goal": getattr(plan_obj, "goal", "Plan"),
            "steps": steps,
            "metadata": getattr(plan_obj, "metadata", {}) or {},
        }

    def _sanitize_windows_command(self, command: str) -> str:
        """Normalize common Unix-style snippets into Windows-compatible commands."""
        command_text = str(command or "").strip()
        if not command_text:
            return command_text

        # source <venv>/bin/activate && pip ...  -> <venv>\Scripts\activate && pip ...
        match = re.search(r"source\s+([^\s]+)/bin/activate\s*&&\s*(.+)", command_text)
        if match:
            env_name = match.group(1).replace("/", "\\")
            tail = match.group(2).strip()
            return f"{env_name}\\Scripts\\activate && {tail}"

        lowered = command_text.lower()
        if "python -m tensorflow install" in lowered:
            return "pip install tensorflow jupyter notebook"
        if lowered.strip() == "jupyter notebook":
            return "python -m notebook"

        return command_text

    def _apply_execution_context(self, plan_data: dict, user_text: str):
        """Inject working directory/cwd defaults and step sanitization before execution."""
        if not isinstance(plan_data, dict):
            return plan_data, None

        steps = plan_data.get("steps", []) if isinstance(plan_data.get("steps", []), list) else []
        working_dir = self._resolve_working_directory()

        project_like_request = any(
            token in (user_text or "").lower()
            for token in ["project", "boilerplate", "setup", "tensorflow", "jupyter", "venv", "virtual environment", "react"]
        )

        requires_directory = False
        rewritten_steps = []
        for step in steps:
            action = (step.get("name") or step.get("tool") or step.get("action") or "").strip()
            params = step.get("args") or step.get("params") or {}
            if not isinstance(params, dict):
                params = {}

            if action == "open_app":
                app_name = str(params.get("app_name", "")).strip().lower()
                if app_name in {"terminal", "cmd"}:
                    params["app_name"] = "powershell"

            if action == "run_command":
                params["command"] = self._sanitize_windows_command(params.get("command", ""))
                if not params.get("cwd"):
                    if working_dir:
                        params["cwd"] = working_dir
                    elif project_like_request:
                        requires_directory = True

            if action in {"create_file", "write_file"}:
                path = str(params.get("path", "")).strip()
                if path.startswith("/") and working_dir:
                    path = os.path.join(working_dir, path.lstrip("/\\"))
                if path and working_dir and not os.path.isabs(path):
                    params["path"] = os.path.join(working_dir, path)
                elif path:
                    params["path"] = path
                elif not path and project_like_request:
                    requires_directory = True

                # LLM often emits create_file(path, content), but create_file only supports path.
                # Split into create_file + write_file for reliable execution.
                if action == "create_file" and "content" in params:
                    content = params.pop("content")
                    rewritten_steps.append({"name": "create_file", "args": dict(params)})
                    rewritten_steps.append({"name": "write_file", "args": {"path": params.get("path", ""), "content": str(content)}})
                    continue

            if action in {"list_directory", "search_files", "open_project", "run_backend_server", "run_frontend"}:
                key = "path" if action != "search_files" else "root"
                if not params.get(key) and working_dir:
                    params[key] = working_dir
                elif not params.get(key) and project_like_request:
                    requires_directory = True

            # Persist normalized shape back into step
            step["name"] = action
            step["args"] = params
            rewritten_steps.append(step)

        if rewritten_steps:
            plan_data["steps"] = rewritten_steps

        if requires_directory and not working_dir:
            return plan_data, (
                "Please provide your project folder path first so I can create files and run commands there. "
                "Example: E:\\Projects\\my-app"
            )

        return plan_data, None

    def _build_reflection_context(self, loop_trace: list):
        """Build a compact context payload for the reflection loop."""
        state = self.memory.get_state()
        return {
            "session": {
                "last_intent": getattr(state, "last_intent", None),
                "last_file_path": getattr(state, "last_file_path", None),
                "last_url": getattr(state, "last_url", None),
                "last_contact": getattr(state, "last_contact", None),
                "facts": getattr(state, "facts", {}) or {},
                "loop_trace": loop_trace[-3:],
            },
            "long_term": {},
        }

    def _memory_command_response(self, text: str):
        """Handle explicit remember/recall user commands before tool planning."""
        return self.memory_commands.process(text)

    def get_last_plan_data(self):
        """Expose latest plan generated by the active agent loop."""
        return self.last_plan_data

    def get_last_loop_trace(self):
        """Expose loop execution trace for diagnostics."""
        return self.last_loop_trace

    def has_pending_confirmation(self):
        """Return whether this controller is waiting for user confirmation."""
        return self.pending_plan is not None

    def get_pending_confirmation(self):
        """Return the latest pending confirmation payload, if any."""
        return self.pending_confirmation_result

    def _finalize_response(self, result: dict, language: str, original_text: str, processed_text: str):
        """Apply output translation and annotate translation metadata."""
        if not isinstance(result, dict):
            return result

        result = self.response_formatter.format(result)

        message = result.get("message", "")
        translated_message, translated_out = self.translation.translate_response_from_english(message, language)
        if translated_out:
            result["message"] = translated_message

        meta = result.get("meta", {})
        if not isinstance(meta, dict):
            meta = {}

        if original_text != processed_text:
            meta["translation"] = {
                "input_language": language,
                "original_command": original_text,
                "translated_command": processed_text,
            }

        if meta:
            result["meta"] = meta

        return result

    def process(self, text: str, language: str = None):
        """Process user input and execute actions.
        
        Args:
            text: User input text.
            
        Returns:
            Result dictionary with status and data.
        """
        try:
            logger.info(f"[AssistantController] Processing: {text}")
            log(f"Input received: {text}")

            active_language = language or assistant_config.get("stt.language", "english")
            processed_text, translated_in = self.translation.translate_command_to_english(text, active_language)
            if translated_in:
                logger.info(f"[AssistantController] Translated command to English: {processed_text}")
                log(f"Input translated to: {processed_text}")

            # Fast-path for explicit memory operations.
            memory_response = self._memory_command_response(processed_text)
            if memory_response:
                self.memory.add_history(memory_response)
                return self._finalize_response(memory_response, active_language, text, processed_text)

            directory_response = self._handle_working_directory_command(processed_text)
            if directory_response:
                self.memory.add_history(directory_response)
                return self._finalize_response(directory_response, active_language, text, processed_text)

            explicit_dir = self._extract_directory_from_text(processed_text)
            if explicit_dir:
                self.memory.update({"last_folder_path": explicit_dir})
                self.memory.remember_fact("working_directory", explicit_dir)

            self.memory.update({"active_goal": self._infer_active_goal(processed_text)})

            loop_history = []
            loop_trace = []
            last_result = None
            last_reflection = None
            self.last_plan_data = None
            self.last_loop_trace = []

            for iteration in range(1, self.max_agent_iterations + 1):
                log(f"User intent detected: planning iteration {iteration}")
                # First pass uses raw user command; later passes include observation context
                if iteration == 1:
                    plan_prompt = f"{self._build_memory_context()}\nUSER COMMAND: {processed_text}"
                else:
                    base_replan = self._build_replan_prompt(processed_text, loop_history, iteration, last_reflection)
                    plan_prompt = f"{self._build_memory_context()}\n{base_replan}"

                intent_data = self.planner.classifier.classify(processed_text, use_llm=True)
                plan_obj = self.planner.create_plan(intent_data, processed_text, self._build_reflection_context(loop_trace))
                plan_data = self._plan_to_dict(plan_obj)
                plan_data, needs_directory = self._apply_execution_context(plan_data, processed_text)
                steps = self._get_plan_steps(plan_data)
                self.last_plan_data = plan_data
                log(f"Plan generated with {len(steps)} step(s)")

                if needs_directory:
                    return self._finalize_response({
                        "status": "needs_input",
                        "message": persona.stylize_response(needs_directory, status="confirmation_required"),
                        "data": {
                            "required": "working_directory",
                            "hint": "Reply with folder path, e.g. E:\\Projects\\my-app",
                        },
                    }, active_language, text, processed_text)

                loop_trace.append({
                    "iteration": iteration,
                    "stage": "plan",
                    "step_count": len(steps),
                    "plan_source": (plan_data.get("metadata", {}) if isinstance(plan_data, dict) else {}).get("plan_source"),
                })

                if not plan_data or not steps:
                    if last_result and last_result.get("status") == "success":
                        break

                    error_msg = persona.stylize_response("I did not understand that command.", status="error")
                    return self._finalize_response({
                        "status": "error",
                        "message": error_msg,
                        "data": {}
                    }, active_language, text, processed_text)

                # Execute current plan attempt
                log("Executing tool steps")
                results = self.multi_executor.execute(plan_data)
                if not results:
                    return self._finalize_response({
                        "status": "error",
                        "message": persona.stylize_response("Execution failed.", status="error"),
                        "data": {}
                    }, active_language, text, processed_text)

                for result in results:
                    self.memory.add_history(result)
                    loop_history.append(result)

                last_result = results[-1]
                loop_trace.append({
                    "iteration": iteration,
                    "stage": "act",
                    "result_status": last_result.get("status"),
                })

                if last_result.get("status") != "confirmation_required":
                    reflection_context = self._build_reflection_context(loop_trace)
                    reflection = self.reflection_engine.analyze(last_result, plan_data, reflection_context)
                    planner_reflection = self.planner.reflect_on_execution(processed_text, plan_data, last_result, reflection_context)
                    if isinstance(planner_reflection, dict) and planner_reflection.get("summary"):
                        reflection["summary"] = planner_reflection.get("summary", reflection.get("summary"))
                    if isinstance(planner_reflection, dict) and planner_reflection.get("memory_updates"):
                        reflection["memory_updates"] = planner_reflection.get("memory_updates", reflection.get("memory_updates", []))
                    if isinstance(planner_reflection, dict) and planner_reflection.get("next_steps"):
                        reflection["next_steps"] = planner_reflection.get("next_steps", reflection.get("next_steps", []))
                    if isinstance(planner_reflection, dict) and planner_reflection.get("should_replan") is not None:
                        reflection["should_replan"] = planner_reflection.get("should_replan", reflection.get("should_replan"))

                    last_reflection = reflection
                    loop_trace.append({
                        "iteration": iteration,
                        "stage": "reflection",
                        "summary": reflection.get("summary"),
                        "should_replan": reflection.get("should_replan"),
                    })
                    self.memory.add_history({
                        "status": "reflection",
                        "message": reflection.get("summary", ""),
                        "data": {
                            "reflection": reflection,
                        },
                    })

                    for memory_update in reflection.get("memory_updates", []):
                        key = memory_update.get("key")
                        value = memory_update.get("value")
                        if key and value is not None:
                            self.memory.remember_fact(str(key), str(value))

                    if last_result.get("status") != "success" and not reflection.get("should_replan", False):
                        logger.warning("[AssistantController] Reflection recommended stopping replans")
                        break

                # Pause loop for user confirmation on critical actions
                if last_result.get("status") == "confirmation_required":
                    self.pending_plan = plan_data
                    self.pending_step_index = last_result.get("step_index", 0)
                    confirm_msg = last_result.get("message", "Confirm action?")
                    confirm_msg = persona.stylize_response(confirm_msg, status="confirmation_required")
                    self.pending_confirmation_result = {
                        "status": "confirmation_required",
                        "message": confirm_msg,
                        "meta": {
                            "loop_trace": loop_trace,
                            "iteration": iteration,
                        },
                        "data": {},
                    }
                    logger.info(f"[AssistantController] Waiting for confirmation: {confirm_msg}")
                    self.last_loop_trace = loop_trace
                    return self._finalize_response(self.pending_confirmation_result, active_language, text, processed_text)

                # Success ends the loop
                if last_result.get("status") == "success":
                    break

                # Non-success triggers another bounded replan iteration
                logger.warning(
                    f"[AssistantController] Iteration {iteration} ended with status="
                    f"{last_result.get('status', 'unknown')}; attempting replan"
                )

                if not last_reflection or not last_reflection.get("should_replan", False):
                    break

            if last_result:
                status = last_result.get("status", "success")
                natural_message = self.response_generator.generate(processed_text, self.last_plan_data or {}, last_result, last_reflection)
                last_result["message"] = natural_message
                clearer_result = self.response_formatter.format(last_result)
                last_result["message"] = persona.stylize_response(clearer_result.get("message", natural_message), status=status)
                last_result["meta"] = {
                    "iterations_used": len({item.get("iteration") for item in loop_trace if item.get("iteration")}),
                    "loop_trace": loop_trace,
                    "reflection": last_reflection,
                }
                self.last_loop_trace = loop_trace
                logger.info(f"[AssistantController] Result: {last_result}")
                return self._finalize_response(last_result, active_language, text, processed_text)

            return self._finalize_response({
                "status": "error",
                "message": persona.stylize_response("Execution failed.", status="error"),
                "meta": {
                    "loop_trace": loop_trace,
                },
                "data": {}
            }, active_language, text, processed_text)
            
        except Exception as e:
            logger.error(f"[AssistantController Error] {e}")
            log(f"Error: {e}")
            error_msg = persona.stylize_response(str(e), status="error")
            return {
                "status": "error",
                "message": error_msg,
                "data": {}
            }

    def confirm_action(self, approved: bool):
        """Handle user confirmation of critical actions.
        
        Args:
            approved: True to approve, False to deny.
            
        Returns:
            Result of the action.
        """
        if not self.pending_plan:
            return {
                "status": "error",
                "message": "No pending action to confirm",
                "data": {}
            }
        
        if approved:
            logger.info("[AssistantController] User approved critical action")
            results = self.multi_executor.approve_confirmation(self.pending_plan, self.pending_step_index)
        else:
            logger.info("[AssistantController] User denied critical action")
            results = [self.multi_executor.deny_confirmation()]
        
        # Clear pending plan
        self.pending_plan = None
        self.pending_confirmation_result = None
        
        # Store in memory
        for result in results:
            self.memory.add_history(result)

        # If continuation hits another critical step, keep the same pending plan
        if results and results[-1].get("status") == "confirmation_required":
            self.pending_step_index = results[-1].get("step_index", self.pending_step_index)
            self.pending_confirmation_result = results[-1]
            return results[-1]

        return results[-1] if results else {"status": "cancelled", "message": "Action cancelled"}