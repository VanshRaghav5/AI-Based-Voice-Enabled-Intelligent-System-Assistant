import json
from backend.llm.llm_client import LLMClient
from backend.core.execution_plan import ExecutionPlan
from backend.core.tool_call import ToolCall


class IntentAgent:

    def __init__(self):
        self.llm = LLMClient()

    def generate_plan(self, text: str, context):

        prompt = self._build_prompt(text, context)

        response = self.llm.generate_plan(prompt)

        if not response or "plan" not in response:
            return ExecutionPlan([])

        steps = []

        for step in response["plan"]:
            steps.append(
                ToolCall(
                    step["intent"],
                    step.get("entities", {})
                )
            )

        return ExecutionPlan(steps)

    def _build_prompt(self, text, context):

        return f"""
You are an AI automation planner.

Current session state:
active_application: {context.active_application}
last_file: {context.last_file_path}
last_contact: {context.last_contact}

User command:
{text}

Return JSON only:
{{
  "plan": [
    {{
      "intent": "tool_name",
      "entities": {{}}
    }}
  ]
}}
"""
