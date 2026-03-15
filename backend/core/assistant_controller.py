from backend.llm.llm_client import LLMClient
from backend.core.tool_registry import ToolRegistry
from backend.core.executor import Executor
from backend.core.multi_executor import MultiExecutor
from backend.memory.session_state import SessionState
from backend.automation.registry_tools import register_all_tools
from backend.config.logger import logger
from backend.config.assistant_config import assistant_config
from backend.core.persona import persona
from backend.core.translation_service import TranslationService
import json
import re


class AssistantController:

    def __init__(self):
        """Initialize the assistant controller with core components."""
        # Initialize LLM client with configured/default model
        self.llm_client = LLMClient()
        
        # Initialize registry and tool executor
        self.registry = ToolRegistry()
        self.executor = Executor(self.registry)
        register_all_tools(self.registry)
        
        # Initialize multi-executor
        self.multi_executor = MultiExecutor(self.registry)
        
        # Initialize session state
        self.memory = SessionState()

        # Optional translator for multi-language command and response handling
        self.translation = TranslationService()
        
        # Track pending plan and step for confirmation
        self.pending_plan = None
        self.pending_step_index = 0

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

    def _build_replan_prompt(self, user_text: str, loop_history: list, iteration: int) -> str:
        """Build a concise prompt for iterative re-planning using prior observations."""
        recent = loop_history[-3:] if loop_history else []
        observation = json.dumps(recent, ensure_ascii=True)
        return (
            f"{user_text}\n\n"
            f"REPLAN ITERATION: {iteration}\n"
            f"RECENT EXECUTION OBSERVATIONS (JSON): {observation}\n"
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

    def _memory_command_response(self, text: str):
        """Handle explicit remember/recall user commands before tool planning."""
        cleaned = text.strip()
        lowered = cleaned.lower()

        remember_match = re.match(r"^remember(?: that)?\s+(.+?)\s+(?:is|are|as)\s+(.+)$", cleaned, flags=re.IGNORECASE)
        if remember_match:
            key = remember_match.group(1).strip()
            value = remember_match.group(2).strip()
            if self.memory.remember_fact(key, value):
                return {
                    "status": "success",
                    "message": persona.stylize_response(f"I will remember that {key} is {value}.", status="success"),
                    "data": {"memory": {"action": "remember", "key": key, "value": value}}
                }

        # Explicit recall patterns: "recall X", "what do you remember about X",
        # "what is my X", "what are my X", "what's my X", "tell me about X"
        recall_match = re.match(
            r"^(?:recall|what do you remember about|tell me about"
            r"|what(?:'s| is| are))\s+(.+?)\??$",
            cleaned, flags=re.IGNORECASE
        )
        if recall_match:
            key = recall_match.group(1).strip().lower()
            value = self.memory.recall_fact(key)
            if value is None:
                return {
                    "status": "error",
                    "message": persona.stylize_response(f"I do not have anything saved for {key}.", status="error"),
                    "data": {"memory": {"action": "recall", "key": key, "found": False}}
                }
            return {
                "status": "success",
                "message": persona.stylize_response(f"You told me {key} is {value}.", status="success"),
                "data": {"memory": {"action": "recall", "key": key, "value": value, "found": True}}
            }

        # Fuzzy recall: if the query looks like a question and a stored key appears in it
        if any(q in lowered for q in ["what", "which", "tell me", "do you know", "do you remember"]):
            facts = self.memory.list_facts()
            matched_key = None
            for fkey in sorted(facts.keys(), key=len, reverse=True):  # longest key first
                if fkey in lowered:
                    matched_key = fkey
                    break
            if matched_key:
                fvalue = facts[matched_key]
                return {
                    "status": "success",
                    "message": persona.stylize_response(f"You told me {matched_key} is {fvalue}.", status="success"),
                    "data": {"memory": {"action": "recall", "key": matched_key, "value": fvalue, "found": True}}
                }

        forget_match = re.match(r"^forget\s+(.+)$", cleaned, flags=re.IGNORECASE)
        if forget_match:
            key = forget_match.group(1).strip().lower()
            removed = self.memory.forget_fact(key)
            if removed:
                return {
                    "status": "success",
                    "message": persona.stylize_response(f"I forgot {key}.", status="success"),
                    "data": {"memory": {"action": "forget", "key": key, "removed": True}}
                }
            return {
                "status": "error",
                "message": persona.stylize_response(f"I could not find {key} in memory.", status="error"),
                "data": {"memory": {"action": "forget", "key": key, "removed": False}}
            }

        if lowered in {"list memory", "show memory", "what do you remember", "show remembered facts"}:
            facts = self.memory.list_facts()
            if not facts:
                return {
                    "status": "success",
                    "message": persona.stylize_response("I do not have any saved facts yet.", status="success"),
                    "data": {"memory": {"action": "list", "facts": {}}}
                }

            preview = "; ".join(f"{k}: {v}" for k, v in list(facts.items())[:10])
            return {
                "status": "success",
                "message": persona.stylize_response(f"Saved memory: {preview}", status="success"),
                "data": {"memory": {"action": "list", "facts": facts}}
            }

        return None

    def get_last_plan_data(self):
        """Expose latest plan generated by the active agent loop."""
        return self.last_plan_data

    def get_last_loop_trace(self):
        """Expose loop execution trace for diagnostics."""
        return self.last_loop_trace

    def _finalize_response(self, result: dict, language: str, original_text: str, processed_text: str):
        """Apply output translation and annotate translation metadata."""
        if not isinstance(result, dict):
            return result

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

            active_language = language or assistant_config.get("stt.language", "english")
            processed_text, translated_in = self.translation.translate_command_to_english(text, active_language)
            if translated_in:
                logger.info(f"[AssistantController] Translated command to English: {processed_text}")

            # Fast-path for explicit memory operations.
            memory_response = self._memory_command_response(processed_text)
            if memory_response:
                self.memory.add_history(memory_response)
                return self._finalize_response(memory_response, active_language, text, processed_text)

            loop_history = []
            loop_trace = []
            last_result = None
            self.last_plan_data = None
            self.last_loop_trace = []

            for iteration in range(1, self.max_agent_iterations + 1):
                # First pass uses raw user command; later passes include observation context
                if iteration == 1:
                    plan_prompt = f"{self._build_memory_context()}\nUSER COMMAND: {processed_text}"
                else:
                    base_replan = self._build_replan_prompt(processed_text, loop_history, iteration)
                    plan_prompt = f"{self._build_memory_context()}\n{base_replan}"

                plan_data = self.llm_client.generate_plan(plan_prompt)
                steps = self._get_plan_steps(plan_data)
                self.last_plan_data = plan_data

                loop_trace.append({
                    "iteration": iteration,
                    "stage": "plan",
                    "step_count": len(steps),
                    "plan_source": getattr(self.llm_client, "last_source", None),
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

                # Pause loop for user confirmation on critical actions
                if last_result.get("status") == "confirmation_required":
                    self.pending_plan = plan_data
                    self.pending_step_index = last_result.get("step_index", 0)
                    confirm_msg = last_result.get("message", "Confirm action?")
                    confirm_msg = persona.stylize_response(confirm_msg, status="confirmation_required")
                    logger.info(f"[AssistantController] Waiting for confirmation: {confirm_msg}")
                    self.last_loop_trace = loop_trace
                    return self._finalize_response({
                        "status": "confirmation_required",
                        "message": confirm_msg,
                        "meta": {
                            "loop_trace": loop_trace,
                            "iteration": iteration,
                        },
                        "data": {}
                    }, active_language, text, processed_text)

                # Success ends the loop
                if last_result.get("status") == "success":
                    break

                # Non-success triggers another bounded replan iteration
                logger.warning(
                    f"[AssistantController] Iteration {iteration} ended with status="
                    f"{last_result.get('status', 'unknown')}; attempting replan"
                )

            if last_result:
                status = last_result.get("status", "success")
                message = last_result.get("message", "Command completed")
                last_result["message"] = persona.stylize_response(message, status=status)
                last_result["meta"] = {
                    "iterations_used": len({item.get("iteration") for item in loop_trace if item.get("iteration")}),
                    "loop_trace": loop_trace,
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
        
        # Store in memory
        for result in results:
            self.memory.add_history(result)

        # If continuation hits another critical step, keep the same pending plan
        if results and results[-1].get("status") == "confirmation_required":
            self.pending_step_index = results[-1].get("step_index", self.pending_step_index)
            return results[-1]

        return results[-1] if results else {"status": "cancelled", "message": "Action cancelled"}