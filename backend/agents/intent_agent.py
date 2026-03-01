"""Intent recognition and understanding agent."""
from __future__ import annotations

from backend.config.logger import logger


class IntentAgent:
    """Agent responsible for understanding user intent from natural language."""

    def __init__(self, llm_client):
        """Initialize the intent agent.
        
        Args:
            llm_client: LLM client instance for intent prediction.
        """
        self.llm_client = llm_client

    def analyze(self, user_input: str) -> dict:
        """Analyze user input and extract intent.
        
        Args:
            user_input: Raw user input text.
            
        Returns:
            Dictionary with intent, entities, and confidence score.
        """
        try:
            logger.info(f"[IntentAgent] Analyzing: {user_input}")
            
            result = self.llm_client.generate(user_input)
            
            logger.info(f"[IntentAgent] Intent result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"[IntentAgent Error] {e}")
            return {
                "intent": "unknown",
                "entities": {},
                "confidence": 0.0
            }
