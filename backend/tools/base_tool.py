# backend/automation/base_tool.py

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    name: str
    description: str
    risk_level: str = "low"  # low | medium | high
    requires_confirmation: bool = False

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        pass

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "risk_level": self.risk_level,
            "requires_confirmation": self.requires_confirmation
        }
