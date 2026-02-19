# backend/automation/whatsapp_desktop.py

import subprocess
import time
import keyboard
import pyautogui
from backend.automation.base_tool import BaseTool


# =========================
# REAL AUTOMATION FUNCTION
# =========================

def send_whatsapp_message(target: str, message: str):
    """
    Send WhatsApp message with proper workflow:
    1. Open WhatsApp
    2. Search contact
    3. Open chat
    4. Type message
    5. Send
    """
    
    # Open WhatsApp
    subprocess.Popen("start whatsapp:", shell=True)
    time.sleep(4)  # Wait for WhatsApp to fully load
    
    try:
        # Open search dialog
        keyboard.press_and_release("ctrl+f")
        time.sleep(1)
        
        # Clear any existing search text
        keyboard.press_and_release("ctrl+a")
        time.sleep(0.3)
        keyboard.press_and_release("delete")
        time.sleep(0.3)
        
        # Type contact name using pyautogui for reliability
        pyautogui.typewrite(target, interval=0.05)
        time.sleep(1)
        
        # Press Enter to select contact
        keyboard.press_and_release("enter")
        time.sleep(2)  # Wait for chat to open
        
        # Now we're in the chat, message field should be active
        # Click somewhere in the middle-lower area to ensure chat window is focused
        pyautogui.click(640, 400)
        time.sleep(0.5)
        
        # Type the message
        if message:
            pyautogui.typewrite(message, interval=0.02)
            time.sleep(0.5)
        
        # Send message with Enter
        keyboard.press_and_release("enter")
        time.sleep(1)
        
    except Exception as e:
        print(f"Error in WhatsApp automation: {e}")
        raise


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
