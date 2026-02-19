# backend/core/assistant_controller.py

from backend.core.agent import Agent
from backend.core.tool_registry import ToolRegistry
from backend.core.executor import Executor
from backend.config.logger import logger

from backend.automation.whatsapp_desktop import WhatsAppSendTool
from backend.automation.registry_tools import register_all_tools

class AssistantController:

    def __init__(self):
        self.agent = Agent()
        self.registry = ToolRegistry()
        self.executor = Executor(self.registry)

        self._register_tools()

    def _register_tools(self):
        register_all_tools(self.registry)

    def process(self, text: str):
        """
        Main processing pipeline:
        Text → Agent → ToolCall → Executor → Tool
        """

        logger.info(f"Processing text: {text}")

        tool_call = self.agent.decide(text)

        logger.info(f"Agent decided: {tool_call.name} with args {tool_call.args}")

        # Unknown command fallback
        if tool_call.name == "unknown":
            return {
                "status": "error",
                "message": "I did not understand that command.",
                "data": {}
            }

        # Execute tool safely
        try:
            result = self.executor.run(tool_call)

            logger.info(f"Tool execution result: {result}")

            return result

        except Exception as e:
            logger.error(f"[Execution Error] {e}")
            return {
                "status": "error",
                "message": "Execution failed.",
                "data": {}
            }
