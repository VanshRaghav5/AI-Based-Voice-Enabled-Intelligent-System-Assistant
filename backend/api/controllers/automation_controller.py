from backend.core.execution.tool_registry import ToolRegistry
from backend.tools.dev_tools import register_all_tools


registry = ToolRegistry()
register_all_tools(registry)



def execute(command: dict) -> dict:
    """
    Central automation dispatcher.
    Expects:
    {
        "intent": "...",
        "target": "...",
        "data": optional
    }
    """

    intent = command.get("intent")
    target = command.get("target")

    try:

        action_map = {
            "open_app": ("open_app", {"app_name": target}),
            "create_file": ("create_file", {"path": target}),
            "open_url": ("open_url", {"url": target}),
            "search_google": ("search_google", {"query": target}),
        }

        mapped = action_map.get(intent)
        if not mapped:
            return {
                "success": False,
                "status": "error",
                "error": "Unsupported intent",
                "message": f"Unsupported intent: {intent}",
            }

        action, params = mapped
        return registry.execute(action, params)

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
