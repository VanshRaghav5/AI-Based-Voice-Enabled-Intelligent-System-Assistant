"""Executor for running tools from the registry."""
from __future__ import annotations

from backend.core.tool_call import ToolCall
from backend.core.tool_registry import ToolRegistry
from backend.config.logger import logger


class Executor:
    """Executes tool calls using the tool registry."""

    def __init__(self, registry: ToolRegistry):
        """Initialize executor with a tool registry.
        
        Args:
            registry: ToolRegistry instance for looking up and executing tools.
        """
        self.registry = registry

    def run(self, tool_call: ToolCall) -> dict:
        """Execute a tool call.
        
        Args:
            tool_call: ToolCall object with name and arguments.
            
        Returns:
            Execution result from the tool.
        """
        try:
            logger.info(f"[Executor] Running tool: {tool_call.name} with args: {tool_call.args}")
            
            result = self.registry.execute(tool_call)
            
            logger.info(f"[Executor] Result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"[Executor Error] {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": {}
            }
