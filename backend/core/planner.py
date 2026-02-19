# backend/core/planner.py

import re
from backend.core.tool_call import ToolCall


class RuleBasedPlanner:

    def plan(self, text: str) -> ToolCall:

        text_lower = text.lower()

        # Example: "send hello to Swayam on whatsapp"
        if "send" in text_lower and "whatsapp" in text_lower:

            # Basic regex extraction
            match = re.search(r"send (.+) to (.+) on whatsapp", text_lower)

            if match:
                message = match.group(1)
                target = match.group(2)

                return ToolCall(
                    name="whatsapp.send",
                    args={
                        "target": target.strip().title(),
                        "message": message.strip()
                    }
                )

        return ToolCall(
            name="unknown",
            args={}
        )
