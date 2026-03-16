import re

from backend.core.persona import persona


class MemoryCommandProcessor:
    """Parse explicit remember, recall, forget, and list-memory commands."""

    def __init__(self, memory_store):
        self.memory = memory_store

    def process(self, text: str):
        """Return a memory result payload when the command is memory-related."""
        cleaned = text.strip()
        lowered = cleaned.lower()

        remember_match = re.match(r"^remember(?: that)?\s+(.+?)\s+(?:is|are|as)\s+(.+)$", cleaned, flags=re.IGNORECASE)
        if remember_match:
            key = remember_match.group(1).strip()
            value = remember_match.group(2).strip()
            if self.memory.remember_fact(key, value):
                return {
                    "status": "success",
                    "message": persona.stylize_response(f"I will remember that {key} is {value}.", status="success"),
                    "data": {"memory": {"action": "remember", "key": key, "value": value}},
                }

        recall_match = re.match(
            r"^(?:recall|what do you remember about|tell me about|what(?:'s| is| are))\s+(.+?)\??$",
            cleaned,
            flags=re.IGNORECASE,
        )
        if recall_match:
            key = recall_match.group(1).strip().lower()
            value = self.memory.recall_fact(key)
            if value is None:
                return {
                    "status": "error",
                    "message": persona.stylize_response(f"I do not have anything saved for {key}.", status="error"),
                    "data": {"memory": {"action": "recall", "key": key, "found": False}},
                }
            return {
                "status": "success",
                "message": persona.stylize_response(f"You told me {key} is {value}.", status="success"),
                "data": {"memory": {"action": "recall", "key": key, "value": value, "found": True}},
            }

        if any(query_token in lowered for query_token in ["what", "which", "tell me", "do you know", "do you remember"]):
            facts = self.memory.list_facts()
            matched_key = None
            for fact_key in sorted(facts.keys(), key=len, reverse=True):
                if fact_key in lowered:
                    matched_key = fact_key
                    break
            if matched_key:
                fact_value = facts[matched_key]
                return {
                    "status": "success",
                    "message": persona.stylize_response(f"You told me {matched_key} is {fact_value}.", status="success"),
                    "data": {"memory": {"action": "recall", "key": matched_key, "value": fact_value, "found": True}},
                }

        forget_match = re.match(r"^forget\s+(.+)$", cleaned, flags=re.IGNORECASE)
        if forget_match:
            key = forget_match.group(1).strip().lower()
            removed = self.memory.forget_fact(key)
            if removed:
                return {
                    "status": "success",
                    "message": persona.stylize_response(f"I forgot {key}.", status="success"),
                    "data": {"memory": {"action": "forget", "key": key, "removed": True}},
                }
            return {
                "status": "error",
                "message": persona.stylize_response(f"I could not find {key} in memory.", status="error"),
                "data": {"memory": {"action": "forget", "key": key, "removed": False}},
            }

        if lowered in {"list memory", "show memory", "what do you remember", "show remembered facts"}:
            facts = self.memory.list_facts()
            if not facts:
                return {
                    "status": "success",
                    "message": persona.stylize_response("I do not have any saved facts yet.", status="success"),
                    "data": {"memory": {"action": "list", "facts": {}}},
                }

            preview = "; ".join(f"{key}: {value}" for key, value in list(facts.items())[:10])
            return {
                "status": "success",
                "message": persona.stylize_response(f"Saved memory: {preview}", status="success"),
                "data": {"memory": {"action": "list", "facts": facts}},
            }

        return None