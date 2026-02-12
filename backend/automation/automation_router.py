from automation.app_launcher import open_app
from automation.system_control import shutdown_system, restart_system, lock_system
from automation.file_manager import create_file, delete_file, open_folder
from automation.browser_control import open_url, search_google, open_youtube


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
    data = command.get("data")

    try:

        # ---------- APP ----------
        if intent == "open_app":
            return open_app(target)

        # ---------- SYSTEM ----------
        elif intent == "shutdown":
            return shutdown_system(confirm=True)

        elif intent == "restart":
            return restart_system(confirm=True)

        elif intent == "lock":
            return lock_system()

        # ---------- FILE ----------
        elif intent == "create_file":
            return create_file(target)

        elif intent == "delete_file":
            return delete_file(target)

        elif intent == "open_folder":
            return open_folder(target)

        # ---------- BROWSER ----------
        elif intent == "open_url":
            return open_url(target)

        elif intent == "search_google":
            return search_google(target)

        elif intent == "open_youtube":
            return open_youtube()

        else:
            return {
                "status": "error",
                "message": f"Unknown intent: {intent}"
            }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
