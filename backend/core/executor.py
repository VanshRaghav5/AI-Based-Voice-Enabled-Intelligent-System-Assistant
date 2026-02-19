# backend/core/executor.py

from backend.core.tool_call import ToolCall
from backend.core.tool_registry import ToolRegistry
from backend.config.logger import logger


class Executor:

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def _confirm_execution(self, tool):
        print(f"⚠ Confirmation required for tool: {tool.name}")
        user_input = input("Type 'yes' to confirm: ")
        return user_input.lower() == "yes"

    def run(self, tool_call: ToolCall):

        try:
            tool = self.registry.get(tool_call.name)

            if not tool:
                return {
                    "status": "error",
                    "message": "Unknown tool",
                    "data": {}
                }

            logger.info(f"Executing tool: {tool_call.name} | args: {tool_call.args}")

            # Confirmation layer
            if tool.requires_confirmation:
                if not self._confirm_execution(tool):
                    return {
                        "status": "cancelled",
                        "message": "Execution cancelled by user.",
                        "data": {}
                    }

            result = tool.execute(**tool_call.args)

            logger.info(f"Tool result: {result}")

            return result

        except Exception as e:
            logger.exception("Tool execution failed")

            return {
                "status": "error",
                "message": str(e),
                "data": {}
            }
