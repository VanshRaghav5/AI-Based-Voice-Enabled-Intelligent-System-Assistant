import re
import subprocess
import time
import urllib.parse

import pyperclip

from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import (
    AutomationError,
    WindowNotFoundError,
    error_handler,
)
from backend.automation.window_detection import window_detector
from backend.config.logger import logger


WHATSAPP_WINDOW_NAME = "WhatsApp"


def _sanitize_phone(raw: str) -> str:
    """Return digits-only phone number, preserving optional leading '+'."""
    text = (raw or "").strip()
    if not text:
        return ""

    keep_plus = text.startswith("+")
    digits = "".join(ch for ch in text if ch.isdigit())
    if keep_plus and digits:
        return f"+{digits}"
    return digits


def _looks_like_phone_target(target: str) -> bool:
    """Treat target as phone number when it has enough digits."""
    cleaned = _sanitize_phone(target)
    return len(cleaned.lstrip("+")) >= 8


def _open_whatsapp_protocol(uri: str) -> None:
    """Open WhatsApp URI via shell."""
    cmd = f'start "" "{uri}"'
    subprocess.Popen(cmd, shell=True)


def _wait_for_whatsapp(timeout: int = 12) -> None:
    if not window_detector.wait_for_window(WHATSAPP_WINDOW_NAME, timeout=timeout):
        raise WindowNotFoundError(
            "WhatsApp window not found",
            "I could not find the WhatsApp window. Please ensure WhatsApp Desktop is installed and running.",
        )


def _focus_whatsapp() -> None:
    if not window_detector.focus_window(WHATSAPP_WINDOW_NAME):
        raise WindowNotFoundError(
            "Could not focus WhatsApp",
            "WhatsApp opened but I could not bring it to the foreground. Please open WhatsApp and try again.",
        )


def _paste_text(text: str) -> None:
    import keyboard

    pyperclip.copy(text)
    keyboard.press_and_release("ctrl+v")


def _open_chat_by_contact(contact_name: str) -> None:
    """Open a chat by searching contact name from WhatsApp global search."""
    import keyboard

    keyboard.press_and_release("ctrl+k")
    time.sleep(0.6)  # Wait for search box to appear

    keyboard.press_and_release("ctrl+a")
    time.sleep(0.15)
    keyboard.press_and_release("delete")
    time.sleep(0.15)

    _paste_text(contact_name)
    time.sleep(1.2)  # Wait for search results to populate

    # Open first likely result.
    keyboard.press_and_release("down")
    time.sleep(0.2)
    keyboard.press_and_release("enter")
    time.sleep(1.5)  # Wait for chat to load


def _send_message_in_active_chat(message: str) -> None:
    """Send message in the currently open chat using clipboard paste + Enter."""
    import keyboard

    # Focus composer via common WhatsApp desktop shortcut.
    time.sleep(0.3)  # Ensure chat fully loaded
    keyboard.press_and_release("ctrl+shift+m")
    time.sleep(0.4)  # Wait for composer to focus and be ready

    _paste_text(message)
    time.sleep(0.2)
    keyboard.press_and_release("enter")
    time.sleep(0.5)  # Wait for message to send


def send_whatsapp_message(target: str, message: str) -> None:
    """Send WhatsApp message via desktop automation with contact or phone target."""
    resolved_target = (target or "").strip()
    resolved_message = (message or "").strip()

    if not resolved_target:
        raise AutomationError(
            "Missing target",
            "I need a WhatsApp contact or phone number to send the message.",
        )

    if not resolved_message:
        raise AutomationError(
            "Missing message",
            "I need the message text before I can send it.",
        )

    logger.info(f"[WhatsApp] Sending message to '{resolved_target}'")

    # Strategy A: phone target via URI deep-link.
    if _looks_like_phone_target(resolved_target):
        phone = _sanitize_phone(resolved_target).lstrip("+")
        encoded = urllib.parse.quote(resolved_message)
        uri = f"whatsapp://send?phone={phone}&text={encoded}"
        _open_whatsapp_protocol(uri)
        _wait_for_whatsapp(timeout=14)
        _focus_whatsapp()
        time.sleep(0.9)

        # Some clients prefill text but do not auto-send.
        import keyboard

        keyboard.press_and_release("enter")
        logger.info("[WhatsApp] Message dispatched via phone deep-link")
        return

    # Strategy B: contact search in Desktop app.
    _open_whatsapp_protocol("whatsapp:")
    _wait_for_whatsapp(timeout=14)
    _focus_whatsapp()
    time.sleep(1.0)  # Give WhatsApp time to fully load UI

    _open_chat_by_contact(resolved_target)
    _focus_whatsapp()
    time.sleep(0.3)  # Ensure fresh focus
    _send_message_in_active_chat(resolved_message)

    logger.info(f"[WhatsApp] Message sent to '{resolved_target}'")


class WhatsAppSendTool(BaseTool):
    name = "whatsapp.send"
    description = "Send a message to a WhatsApp contact"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, target: str = None, message: str = None, contact: str = None, data: str = None, body: str = None):
        resolved_target = (target or contact or "").strip()
        resolved_message = (message or data or body or "").strip()

        if not resolved_target:
            return {
                "status": "error",
                "message": "Missing WhatsApp contact name or phone number",
                "data": {"required": ["target/contact", "message/body"]},
            }

        if not resolved_message:
            return {
                "status": "error",
                "message": "Missing WhatsApp message text",
                "data": {"required": ["target/contact", "message/body"]},
            }

        def _send():
            send_whatsapp_message(resolved_target, resolved_message)
            return {
                "status": "success",
                "message": f"Message sent to {resolved_target} on WhatsApp",
                "data": {
                    "target": resolved_target,
                    "message_length": len(resolved_message),
                    "target_type": "phone" if _looks_like_phone_target(resolved_target) else "contact",
                },
            }

        return error_handler.wrap_automation(
            func=_send,
            operation_name="WhatsApp Send Message",
            context={"app": "WhatsApp", "target": resolved_target},
        )


class WhatsAppDesktop:
    """Compatibility wrapper used by automation router."""

    def open_app(self) -> bool:
        try:
            _open_whatsapp_protocol("whatsapp:")
            _wait_for_whatsapp(timeout=10)
            _focus_whatsapp()
            return True
        except Exception as e:
            logger.error(f"[WhatsApp] open_app failed: {e}")
            return False

    def open_chat(self, target: str) -> bool:
        try:
            if _looks_like_phone_target(target):
                phone = _sanitize_phone(target).lstrip("+")
                _open_whatsapp_protocol(f"whatsapp://send?phone={phone}")
                _wait_for_whatsapp(timeout=12)
                _focus_whatsapp()
                return True

            if not self.open_app():
                return False

            _open_chat_by_contact((target or "").strip())
            return True
        except Exception as e:
            logger.error(f"[WhatsApp] open_chat failed: {e}")
            return False

    def send_message(self, target: str, message: str) -> bool:
        try:
            send_whatsapp_message(target, message)
            return True
        except Exception as e:
            logger.error(f"[WhatsApp] send_message failed: {e}")
            return False


class WhatsAppOpenTool(BaseTool):
    name = "whatsapp.open"
    description = "Open WhatsApp Desktop"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        def _open():
            desktop = WhatsAppDesktop()
            if desktop.open_app():
                return {
                    "status": "success",
                    "message": "WhatsApp opened successfully",
                    "data": {},
                }
            raise WindowNotFoundError(
                "WhatsApp failed to open",
                "I could not open WhatsApp. Please ensure it is installed.",
            )

        return error_handler.wrap_automation(
            func=_open,
            operation_name="Open WhatsApp",
            context={"app": "WhatsApp"},
        )


class WhatsAppOpenChatTool(BaseTool):
    name = "whatsapp.open_chat"
    description = "Open WhatsApp Desktop and open chat with target"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, target: str):
        def _open_chat():
            desktop = WhatsAppDesktop()
            if desktop.open_chat(target):
                return {
                    "status": "success",
                    "message": f"Opened chat with {target}",
                    "data": {"target": target},
                }
            raise AutomationError(
                f"Failed to open chat with {target}",
                f"I could not open the chat with {target}. Please verify the contact exists in WhatsApp.",
            )

        return error_handler.wrap_automation(
            func=_open_chat,
            operation_name="Open WhatsApp Chat",
            context={"app": "WhatsApp", "target": target},
        )
