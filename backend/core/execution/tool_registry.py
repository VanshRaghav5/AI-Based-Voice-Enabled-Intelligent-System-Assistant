from typing import Callable, Dict, List
from backend.utils.logger import log


class ToolRegistry:

    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        self.tools[name] = func

    def execute(self, action: str, params: dict):
        log(f"Executing step: {action}")
        if action not in self.tools:
            log(f"Error: tool not found -> {action}")
            return {"success": False, "error": "Tool not found"}

        try:
            return self.tools[action](**(params or {}))
        except Exception as e:
            log(f"Error while executing {action}: {e}")
            return {"success": False, "error": str(e)}

    def get(self, name: str):
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())
