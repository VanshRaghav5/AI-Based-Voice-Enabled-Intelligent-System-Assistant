"""Tool agent for executing registered tools."""
from __future__ import annotations

from backend.config.logger import logger


class ToolAgent:
    """Agent responsible for selecting and executing tools."""

    def __init__(self, executor, registry):
        """Initialize the tool agent.
        
        Args:
            executor: Executor instance for running tools.
            registry: Tool registry for looking up available tools.
        """
        self.executor = executor
        self.registry = registry

    def execute(self, tool_name: str, params: dict) -> dict:
        """Execute a tool with given parameters.
        
        Args:
            tool_name: Name of the tool to execute.
            params: Parameters for the tool.
            
        Returns:
            Execution result dictionary.
        """
        try:
            logger.info(f"[ToolAgent] Executing tool: {tool_name}")
            
            # Create tool call
            from backend.core.tool_call import ToolCall
            tool_call = ToolCall(name=tool_name, params=params)
            
            # Execute the tool
            result = self.executor.run(tool_call)
            
            logger.info(f"[ToolAgent] Tool result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"[ToolAgent Error] {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": {}
            }
