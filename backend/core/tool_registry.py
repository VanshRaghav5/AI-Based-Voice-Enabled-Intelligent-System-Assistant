# backend/core/tool_registry.py

from typing import Dict, List
from backend.core.tool_call import ToolCall
from backend.automation.base_tool import BaseTool


class ToolRegistry:

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        return self._tools.get(name)

    def execute(self, tool_call: ToolCall):
        tool = self.get(tool_call.name)

        if not tool:
            raise ValueError(f"Tool '{tool_call.name}' not found.")

        return tool.execute(**tool_call.args)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_tool_manifest(self):
        return [tool.metadata() for tool in self._tools.values()]
