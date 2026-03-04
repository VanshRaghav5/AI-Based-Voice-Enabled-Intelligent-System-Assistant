# backend/automation/whatsapp_desktop.py

import subprocess
import time
import pyperclip
from backend.automation.base_tool import BaseTool
from backend.automation.window_detection import window_detector
from backend.automation.error_handler import error_handler, WindowNotFoundError, AutomationTimeoutError, AutomationError
from backend.config.logger import logger


# =========================
# REAL AUTOMATION FUNCTION
# =========================

def send_whatsapp_message(target: str, message: str):
    """
    Send WhatsApp message with proper workflow:
    1. Open WhatsApp
    2. Verify window is active
    3. Search contact via clipboard paste
    4. Open chat
    5. Type message via clipboard paste
    6. Send
    """
    import keyboard
    import pyautogui

    try:
        # Open WhatsApp
        logger.info(f"Opening WhatsApp to send message to {target}")
        subprocess.Popen("start whatsapp:", shell=True)
        time.sleep(3)

        # Wait for WhatsApp window to appear
        if not window_detector.wait_for_window("WhatsApp", timeout=10):
            raise WindowNotFoundError(
                "WhatsApp window not found after opening",
                "I couldn't find the WhatsApp window. Please make sure WhatsApp is installed and try again."
            )

        time.sleep(2)

        # Ensure WhatsApp window is focused
        if not window_detector.focus_window("WhatsApp"):
            logger.warning("Could not focus WhatsApp window, continuing anyway")

        time.sleep(0.5)

        # Open search dialog
        logger.info(f"Searching for contact: {target}")
        keyboard.press_and_release("ctrl+f")
        time.sleep(1)

        # Clear any existing search text
        keyboard.press_and_release("ctrl+a")
        time.sleep(0.2)
        keyboard.press_and_release("delete")
        time.sleep(0.2)

        # Paste contact name via clipboard (handles all characters)
        pyperclip.copy(target)
        keyboard.press_and_release("ctrl+v")
        time.sleep(1.5)

        # Press Enter to open the contact's chat
        keyboard.press_and_release("enter")
        time.sleep(2)

        # Press Escape to close search and land in the chat, then Tab to message box
        keyboard.press_and_release("escape")
        time.sleep(0.5)

        # Click at bottom-center to focus message input box
        # Use a relative position: bottom 10% of screen, horizontal center
        screen_w, screen_h = pyautogui.size()
        msg_x = screen_w // 2
        msg_y = int(screen_h * 0.93)
        logger.info(f"Clicking message input at ({msg_x}, {msg_y})")
        pyautogui.click(msg_x, msg_y)
        time.sleep(0.5)

        # Clear any existing text in message box
        keyboard.press_and_release("ctrl+a")
        time.sleep(0.2)

        # Paste message via clipboard (handles unicode, emojis, special chars)
        logger.info(f"Typing message: {message}")
        pyperclip.copy(message)
        keyboard.press_and_release("ctrl+v")
        time.sleep(0.5)

        # Send message
        logger.info("Sending message...")
        keyboard.press_and_release("enter")
        time.sleep(1)

        logger.info(f"Successfully sent WhatsApp message to {target}: '{message}'")

    except (WindowNotFoundError, AutomationTimeoutError) as e:
        logger.error(f"WhatsApp automation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in WhatsApp automation: {e}", exc_info=True)
        raise AutomationError(
            str(e),
            f"Failed to send WhatsApp message: {str(e)}"
        )


# =========================
# TOOL WRAPPER
# =========================

class WhatsAppSendTool(BaseTool):
    name = "whatsapp.send"
    description = "Send a message to a WhatsApp contact"
    risk_level = "medium"
    requires_confirmation = True

    def execute(self, target: str, message: str):
        """Execute WhatsApp message send with comprehensive error handling"""
        
        def _send():
            send_whatsapp_message(target, message)
            return {
                "status": "success",
                "message": f"Message sent to {target} on WhatsApp",
                "data": {"target": target, "message_length": len(message)}
            }
        
        # Wrap with error handler for consistent error messages
        return error_handler.wrap_automation(
            func=_send,
            operation_name="WhatsApp Send Message",
            context={"app": "WhatsApp", "target": target}
        )


# Compatibility wrapper used by automation_router
class WhatsAppDesktop:
    """High-level interface used by the automation router.

    Methods:
        open_app() -> bool
        open_chat(target: str) -> bool
        send_message(target: str, message: str) -> bool
    """

    def open_app(self) -> bool:
        """Open WhatsApp Desktop application"""
        try:
            logger.info("Opening WhatsApp Desktop")
            subprocess.Popen("start whatsapp:", shell=True)
            time.sleep(2)
            
            # Verify it opened
            if window_detector.wait_for_window("WhatsApp", timeout=8):
                logger.info("WhatsApp opened successfully")
                return True
            else:
                logger.warning("WhatsApp window not detected")
                return False
                
        except Exception as e:
            logger.error(f"Failed to open WhatsApp: {e}")
            return False
    
    def open_chat(self, target: str) -> bool:
        """Open a specific chat in WhatsApp"""
        try:
            # Ensure app is open
            if not window_detector.is_window_active("WhatsApp", timeout=2):
                logger.info("WhatsApp not open, opening now")
                if not self.open_app():
                    return False
            
            time.sleep(1)
            
            # Focus WhatsApp window
            window_detector.focus_window("WhatsApp")
            time.sleep(0.5)

            # Open search and paste contact name via clipboard (handles all chars)
            import keyboard

            keyboard.press_and_release("ctrl+f")
            time.sleep(0.5)
            keyboard.press_and_release("ctrl+a")
            time.sleep(0.2)
            keyboard.press_and_release("delete")
            time.sleep(0.2)

            pyperclip.copy(target)
            keyboard.press_and_release("ctrl+v")

            time.sleep(0.8)
            keyboard.press_and_release("enter")
            time.sleep(1.2)
            
            logger.info(f"Opened chat with {target}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open chat: {e}")
            return False

    def send_message(self, target: str, message: str) -> bool:
        """Send a message to a contact"""
        try:
            # Reuse the lower-level function which handles full flow
            send_whatsapp_message(target, message)
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False


# Non-critical tools to open the app or a chat (registered separately)
class WhatsAppOpenTool(BaseTool):
    name = "whatsapp.open"
    description = "Open WhatsApp Desktop"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        """Open WhatsApp Desktop with error handling"""
        
        def _open():
            w = WhatsAppDesktop()
            success = w.open_app()
            
            if success:
                return {
                    "status": "success",
                    "message": "WhatsApp opened successfully",
                    "data": {}
                }
            else:
                raise WindowNotFoundError(
                    "WhatsApp failed to open",
                    "I couldn't open WhatsApp. Please make sure it's installed on your computer."
                )
        
        return error_handler.wrap_automation(
            func=_open,
            operation_name="Open WhatsApp",
            context={"app": "WhatsApp"}
        )


class WhatsAppOpenChatTool(BaseTool):
    name = "whatsapp.open_chat"
    description = "Open WhatsApp Desktop and open chat with target"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, target: str):
        """Open a WhatsApp chat with error handling"""
        
        def _open_chat():
            w = WhatsAppDesktop()
            success = w.open_chat(target)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Opened chat with {target}",
                    "data": {"target": target}
                }
            else:
                raise AutomationError(
                    f"Failed to open chat with {target}",
                    f"I couldn't open the chat with {target}. Please verify the contact exists in WhatsApp."
                )
        
        return error_handler.wrap_automation(
            func=_open_chat,
            operation_name="Open WhatsApp Chat",
            context={"app": "WhatsApp", "target": target}
        )
