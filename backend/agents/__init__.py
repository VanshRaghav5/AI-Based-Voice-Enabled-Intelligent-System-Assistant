"""Agent modules for multi-agent orchestration.

This module exports the three core agent contracts:
1. brain_router.route - Decides task vs chat mode
2. intent_agent.plan - Converts input to ExecutionPlan (Task Brain)
3. chat_agent.respond - Generates conversational responses

Design principle: Agents never call each other directly.
The controller wires them together.
"""

from backend.agents.brain_router import route
from backend.agents.intent_agent import plan
from backend.agents.chat_agent import respond

__all__ = [
    "route",      # Mode classification (task/chat)
    "plan",       # Task planning (ExecutionPlan)
    "respond",    # Conversational responses
]

