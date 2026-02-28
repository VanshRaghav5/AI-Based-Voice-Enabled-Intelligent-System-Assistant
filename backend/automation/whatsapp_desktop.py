# backend/automation/whatsapp_desktop.py

import subprocess
import time
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
    3. Search contact
    4. Open chat
    5. Type message
    6. Send
    """
    
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
        
        # Give additional time for full load
        time.sleep(2)
        
        # Ensure WhatsApp window is focused
        if not window_detector.focus_window("WhatsApp"):
            logger.warning("Could not focus WhatsApp window, continuing anyway")
        
        # Import automation libraries
        try:
            import keyboard
            import pyautogui
        except ImportError as e:
            logger.error(f"Required automation libraries not available: {e}")
            raise AutomationError(
                f"Missing automation library: {e}",
                "The automation tools are not properly installed. Please contact support."
            )
        
        # Open search dialog
        logger.debug("Opening search dialog")
        keyboard.press_and_release("ctrl+f")
        time.sleep(1)
        
        # Clear any existing search text
        keyboard.press_and_release("ctrl+a")
        time.sleep(0.3)
        keyboard.press_and_release("delete")
        time.sleep(0.3)
        
        # Type contact name with error handling
        logger.debug(f"Searching for contact: {target}")
        try:
            pyautogui.typewrite(target, interval=0.05)
        except Exception as e:
            logger.error(f"Error typing contact name: {e}")
            # Fallback to keyboard typing
            keyboard.write(target)
        
        time.sleep(1.5)
        
        # Press Enter to select contact
        keyboard.press_and_release("enter")
        time.sleep(2)  # Wait for chat to open
        
        # Click in message area to ensure focus
        try:
            pyautogui.click(640, 400)
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"Could not click message area: {e}")
        
        # Type the message
        if message:
            logger.debug("Typing message")
            try:
                pyautogui.typewrite(message, interval=0.02)
            except Exception as e:
                logger.error(f"Error typing message with pyautogui: {e}")
                # Fallback to keyboard
                keyboard.write(message)
            
            time.sleep(0.5)
        else:
            logger.warning("No message content provided")
            raise ValueError("Message content is required")
        
        # Send message with Enter
        logger.debug("Sending message")
        keyboard.press_and_release("enter")
        time.sleep(1)
        
        logger.info(f"Successfully sent WhatsApp message to {target}")
        
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

            # Open search and type contact name
            import keyboard
            import pyautogui

            keyboard.press_and_release("ctrl+f")
            time.sleep(0.5)
            keyboard.press_and_release("ctrl+a")
            time.sleep(0.2)
            keyboard.press_and_release("delete")
            time.sleep(0.2)
            
            try:
                pyautogui.typewrite(target, interval=0.05)
            except:
                keyboard.write(target)
            
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
