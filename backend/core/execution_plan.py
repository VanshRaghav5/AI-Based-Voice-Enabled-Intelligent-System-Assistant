from typing import List
from backend.core.tool_call import ToolCall


class ExecutionPlan:

    def __init__(self, steps: List[ToolCall]):
        self.steps = steps

    def is_empty(self):
        return len(self.steps) == 0
