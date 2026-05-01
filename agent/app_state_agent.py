import platform
from typing import Any

import psutil

from actions.computer_control import computer_control
from actions.open_app import open_app


_OS = platform.system()


def _is_process_running(process_hint: str) -> bool:
    hint = process_hint.lower().strip()
    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if hint in name:
                return True
        except Exception:
            continue
    return False


def _ensure_app_open(app_name: str, process_hint: str | None = None) -> str:
    hint = process_hint or app_name
    if _is_process_running(hint):
        return f"{app_name} is already running."
    return open_app(parameters={"app_name": app_name})


def app_state_agent(parameters: dict | None = None, player=None) -> str:
    params = parameters or {}
    action = str(params.get("action", "")).lower().strip()

    if action == "send_whatsapp_message":
        receiver = str(params.get("receiver", "")).strip()
        message = str(params.get("message_text", "")).strip()
        if not receiver or not message:
            return "receiver and message_text are required"

        open_result = _ensure_app_open("WhatsApp", "whatsapp")
        computer_control(parameters={"action": "wait", "seconds": 1.2})
        computer_control(parameters={"action": "hotkey", "keys": "ctrl+f"})
        computer_control(parameters={"action": "smart_type", "text": receiver, "clear_first": True})
        computer_control(parameters={"action": "press", "key": "enter"})
        computer_control(parameters={"action": "smart_type", "text": message})
        computer_control(parameters={"action": "press", "key": "enter"})
        return f"State-aware WhatsApp flow executed. {open_result}"

    if action == "check_app_state":
        app_name = str(params.get("app_name", "")).strip()
        if not app_name:
            return "app_name is required"
        running = _is_process_running(app_name)
        return f"{app_name} is {'running' if running else 'not running'}."

    return "Unknown action. Use: send_whatsapp_message, check_app_state."
