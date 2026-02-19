# backend/core/tool_call.py

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]
