"""Safety agent for risk assessment and confirmation."""
from __future__ import annotations

from backend.config.logger import logger


class SafetyAgent:
    """Agent responsible for assessing risks and enforcing safety policies."""

    RISK_LEVELS = {
        "low": 0,
        "medium": 1,
        "high": 2,
        "critical": 3,
    }

    def __init__(self):
        """Initialize the safety agent."""
        pass

    def assess_risk(self, tool_name: str, registry) -> str:
        """Assess the risk level of a tool.
        
        Args:
            tool_name: Name of the tool to assess.
            registry: Tool registry for looking up tool properties.
            
        Returns:
            Risk level as string: 'low', 'medium', 'high', or 'critical'.
        """
        try:
            logger.info(f"[SafetyAgent] Assessing risk for: {tool_name}")
            
            tool = registry.get(tool_name)
            if tool:
                risk_level = getattr(tool, "risk_level", "medium")
                logger.info(f"[SafetyAgent] Risk level: {risk_level}")
                return risk_level
            
            return "medium"
            
        except Exception as e:
            logger.error(f"[SafetyAgent Error] {e}")
            return "high"

    def requires_confirmation(self, tool_name: str, registry) -> bool:
        """Check if a tool requires user confirmation.
        
        Args:
            tool_name: Name of the tool.
            registry: Tool registry.
            
        Returns:
            True if confirmation is required, False otherwise.
        """
        try:
            tool = registry.get(tool_name)
            if tool:
                return getattr(tool, "requires_confirmation", False)
            return False
            
        except Exception as e:
            logger.error(f"[SafetyAgent Error] {e}")
            return True
