"""Planning agent for multi-step task execution."""
from __future__ import annotations

from typing import List
from backend.config.logger import logger


class PlannerAgent:
    """Agent responsible for breaking down tasks into executable steps."""

    def __init__(self):
        """Initialize the planner agent."""
        pass

    def plan(self, intent: str, entities: dict) -> List[dict]:
        """Create an execution plan from intent and entities.
        
        Args:
            intent: Identified intent from IntentAgent.
            entities: Extracted entities from user input.
            
        Returns:
            List of execution steps with tool names and parameters.
        """
        try:
            logger.info(f"[PlannerAgent] Planning for intent: {intent}")
            
            # Build execution steps based on intent
            steps = self._build_steps(intent, entities)
            
            logger.info(f"[PlannerAgent] Generated {len(steps)} steps")
            return steps
            
        except Exception as e:
            logger.error(f"[PlannerAgent Error] {e}")
            return []

    def _build_steps(self, intent: str, entities: dict) -> List[dict]:
        """Build execution steps from intent and entities.
        
        Args:
            intent: Intent identifier.
            entities: Extracted entities.
            
        Returns:
            List of step dictionaries.
        """
        steps = []
        
        # Map intents to tool sequences
        intent_map = {
            "file_open": [{"tool": "file.open", "params": {"path": entities.get("path")}}],
            "file_create": [{"tool": "file.create", "params": {"path": entities.get("path")}}],
            "file_delete": [{"tool": "file.delete", "params": {"path": entities.get("path")}}],
            "file_move": [{"tool": "file.move", "params": {"source": entities.get("source"), "destination": entities.get("destination")}}],
            "folder_create": [{"tool": "folder.create", "params": {"path": entities.get("path")}}],
            "folder_delete": [{"tool": "folder.delete", "params": {"path": entities.get("path")}}],
        }
        
        return intent_map.get(intent, [])
