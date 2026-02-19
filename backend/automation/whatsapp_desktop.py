# backend/automation/whatsapp_desktop.py

import subprocess
import time
import keyboard
from backend.automation.base_tool import BaseTool


# =========================
# REAL AUTOMATION FUNCTION
# =========================

def send_whatsapp_message(target: str, message: str):

    # Example structure (replace with your real working code)

    # Open WhatsApp
    subprocess.Popen("start whatsapp:", shell=True)
    time.sleep(3)

    # Focus search
    keyboard.press_and_release("ctrl+f")
    time.sleep(1)

    # Type contact name
    keyboard.write(target)
    time.sleep(1)

    keyboard.press_and_release("enter")
    time.sleep(1)

    # Type message
    keyboard.write(message)
    time.sleep(0.5)

    keyboard.press_and_release("enter")


# =========================
# TOOL WRAPPER
# =========================

class WhatsAppSendTool(BaseTool):
    name = "whatsapp.send"
    description = "Send a message to a WhatsApp contact"
    risk_level = "medium"
    requires_confirmation = True

    def execute(self, target: str, message: str):

        try:
            send_whatsapp_message(target, message)

            return {
                "status": "success",
                "message": f"Message sent to {target}",
                "data": {}
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "data": {}
            }
