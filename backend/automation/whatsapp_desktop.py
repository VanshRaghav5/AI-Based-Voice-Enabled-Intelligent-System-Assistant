import subprocess
import time
import urllib.parse
from typing import Optional, Tuple
import re

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
WHATSAPP_BOOT_TIMEOUT = 16
CONTACT_OPEN_ATTEMPTS = 3


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


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


def _contact_search_variants(target: str) -> list[str]:
    """Generate search variants that prefer exact matches for short names."""
    cleaned = (target or "").strip()
    if not cleaned:
        return []

    variants = [cleaned]

    # For short single-token names, try exact-ish variants first to avoid substring hits.
    if " " not in cleaned and len(cleaned) <= 8:
        # Avoid quoted text: WhatsApp search treats quotes as literal characters.
        variants = [cleaned, f"{cleaned} ", cleaned.lower(), cleaned.title()]

    # Preserve order and remove duplicates.
    seen = set()
    ordered = []
    for v in variants:
        key = v.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(v)
    return ordered


def _normalize_message_for_target(message: str, target: str) -> str:
    """Remove command residue from message text before sending.

    Examples cleaned:
    - "send testing to swayam gla on whatsapp" -> "testing"
    - "testing to swayam gla" -> "testing"
    """
    raw_message = (message or "").strip()
    raw_target = (target or "").strip()
    if not raw_message:
        return ""

    cleaned = raw_message
    cleaned = re.sub(r'^(?:send\s+)?(?:message\s+|msg\s+|text\s+)?', '', cleaned, flags=re.IGNORECASE).strip()

    if raw_target:
        target_re = re.escape(raw_target)

        # Full command-like phrase.
        pattern_full = re.compile(
            rf'^(.*?)\s+(?:to|for)\s+{target_re}(?:\s+on\s+whats?\s*app)?\s*$',
            flags=re.IGNORECASE,
        )
        m = pattern_full.match(cleaned)
        if m:
            candidate = m.group(1).strip(" .,!?")
            if candidate:
                cleaned = candidate

        # Fallback trailing residue only.
        cleaned = re.sub(
            rf'\s+(?:to|for)\s+{target_re}(?:\s+on\s+whats?\s*app)?\s*$',
            '',
            cleaned,
            flags=re.IGNORECASE,
        ).strip(" .,!?")

    return cleaned or raw_message


def _open_whatsapp_protocol(uri: str) -> None:
    """Open WhatsApp URI via shell."""
    cmd = f'start "" "{uri}"'
    subprocess.Popen(cmd, shell=True)


def _wait_for_whatsapp(timeout: int = WHATSAPP_BOOT_TIMEOUT) -> None:
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


def _send_hotkey(*keys: str) -> None:
    """Send a hotkey chord with pyautogui first, keyboard fallback second."""
    combo = [k.lower() for k in keys if k]
    if not combo:
        return

    try:
        import pyautogui

        pyautogui.hotkey(*combo)
        return
    except Exception:
        pass

    import keyboard

    keyboard.press_and_release("+".join(combo))


def _press_key(key: str) -> None:
    """Press one key with pyautogui first, keyboard fallback second."""
    key_name = (key or "").lower().strip()
    if not key_name:
        return

    try:
        import pyautogui

        pyautogui.press(key_name)
        return
    except Exception:
        pass

    import keyboard

    keyboard.press_and_release(key_name)


def _paste_text(text: str) -> None:
    pyperclip.copy(text)
    _send_hotkey("ctrl", "v")


def _get_whatsapp_window_rect() -> Optional[Tuple[int, int, int, int]]:
    """Return WhatsApp window rect as (left, top, width, height)."""
    try:
        import pygetwindow as gw

        windows = gw.getWindowsWithTitle(WHATSAPP_WINDOW_NAME)
        if not windows:
            return None

        window = windows[0]
        return int(window.left), int(window.top), int(window.width), int(window.height)
    except Exception:
        return None


def _click_relative(x_ratio: float, y_ratio: float, double: bool = False) -> bool:
    """Click inside WhatsApp by relative coordinates; returns True on successful click."""
    rect = _get_whatsapp_window_rect()
    if rect is None:
        return False

    left, top, width, height = rect
    x = int(left + (width * x_ratio))
    y = int(top + (height * y_ratio))

    try:
        import pyautogui

        if double:
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.click(x, y)
        return True
    except Exception:
        return False


def _focus_and_prime_ui() -> None:
    """Bring WhatsApp to front and close transient overlays."""
    _focus_whatsapp()
    _sleep(0.20)
    _press_key("esc")
    _sleep(0.10)


def _open_new_chat_dialog() -> None:
    """Open WhatsApp new-chat picker where contact search is deterministic."""
    _send_hotkey("ctrl", "n")
    _sleep(0.70)


def _open_search_box() -> None:
    """Open left-side search box via keyboard only."""
    _send_hotkey("ctrl", "k")
    _sleep(0.45)


def _clear_search_box() -> None:
    _send_hotkey("ctrl", "a")
    _sleep(0.12)
    _press_key("backspace")
    _sleep(0.12)


def _search_contact(contact_name: str) -> None:
    _open_search_box()
    _clear_search_box()
    _paste_text(contact_name)
    _sleep(1.20)


def _search_contact_in_new_chat(contact_name: str) -> None:
    _open_new_chat_dialog()
    _clear_search_box()
    _paste_text(contact_name)
    _sleep(1.10)


def _open_first_result_with_mouse() -> bool:
    """Attempt to open first visible result in left pane by clicking likely rows."""
    candidate_rows = [0.52, 0.58, 0.64, 0.70]

    for row in candidate_rows:
        if _click_relative(0.22, row, double=True):
            _sleep(0.40)
            return True

    return False


def _open_first_result_with_keyboard() -> None:
    """Fallback keyboard navigation from search box to first result row."""
    _press_key("down")
    _sleep(0.20)
    _press_key("enter")
    _sleep(0.80)


def _open_chat_by_contact(contact_name: str) -> None:
    """Open a chat by searching contact name from WhatsApp chat search."""
    resolved_contact = (contact_name or "").strip()
    if not resolved_contact:
        raise AutomationError(
            "Missing contact",
            "I need the contact name to open the WhatsApp chat.",
        )

    last_error: Optional[Exception] = None

    for attempt in range(1, CONTACT_OPEN_ATTEMPTS + 1):
        try:
            logger.info(f"[WhatsApp] Opening contact '{resolved_contact}' (attempt {attempt})")
            _focus_and_prime_ui()

            opened = False
            for variant in _contact_search_variants(resolved_contact):
                _search_contact_in_new_chat(variant)

                # Open the currently matched contact directly.
                # Do not force Down-to-top-row selection: that can open unrelated chats.
                _press_key("enter")
                _sleep(0.80)

                # Some builds require a second confirm Enter, still without moving selection.
                _press_key("enter")
                _sleep(0.55)
                opened = True
                break

            if not opened:
                raise AutomationError(
                    f"Could not resolve contact {resolved_contact}",
                    f"I could not find a chat for {resolved_contact} on WhatsApp.",
                )

            _focus_whatsapp()
            _sleep(0.25)
            return
        except Exception as e:
            last_error = e
            logger.warning(f"[WhatsApp] Contact open attempt {attempt} failed: {e}")
            _sleep(0.40)

    raise AutomationError(
        f"Failed to open chat for {resolved_contact}",
        f"I could not open the chat with {resolved_contact}. Please verify the contact exists in WhatsApp.",
        details={"contact": resolved_contact, "last_error": str(last_error) if last_error else None},
    )


def _focus_message_composer() -> None:
    """Focus chat composer without leaving the opened conversation."""
    _focus_whatsapp()
    _sleep(0.10)

    # Click composer in right pane. This is safer than ESC chaining,
    # which can back out of the just-opened contact flow.
    if _click_relative(0.72, 0.94):
        _sleep(0.12)
        return

    # Keyboard fallback when click is unavailable.
    _press_key("tab")
    _sleep(0.10)


def _send_message_in_active_chat(message: str) -> None:
    """Send message in the currently open chat using clipboard paste + Enter."""
    resolved_message = (message or "").strip()
    if not resolved_message:
        raise AutomationError("Missing message", "I need the message text before I can send it.")

    _focus_whatsapp()
    _sleep(0.10)
    _focus_message_composer()

    _paste_text(resolved_message)
    _sleep(0.20)
    _press_key("enter")
    _sleep(0.45)


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
        _wait_for_whatsapp(timeout=WHATSAPP_BOOT_TIMEOUT)
        _focus_and_prime_ui()

        # Some clients prefill text but do not auto-send.
        _press_key("enter")
        logger.info("[WhatsApp] Message dispatched via phone deep-link")
        return

    # Strategy B: contact search in Desktop app.
    _open_whatsapp_protocol("whatsapp:")
    _wait_for_whatsapp(timeout=WHATSAPP_BOOT_TIMEOUT)
    _focus_and_prime_ui()
    _sleep(1.00)

    _open_chat_by_contact(resolved_target)
    _send_message_in_active_chat(resolved_message)

    logger.info(f"[WhatsApp] Message sent to '{resolved_target}'")


class WhatsAppSendTool(BaseTool):
    name = "whatsapp.send"
    description = "Send a message to a WhatsApp contact"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, target: str = None, message: str = None, contact: str = None, data: str = None, body: str = None):
        resolved_target = (target or contact or "").strip()
        resolved_message = _normalize_message_for_target((message or data or body or "").strip(), resolved_target)
        target_norm = " ".join(resolved_target.lower().split())
        message_norm = " ".join(resolved_message.lower().split())

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

        # Safety: block likely parser swap where message becomes the contact name.
        if target_norm and message_norm and target_norm == message_norm and not _looks_like_phone_target(resolved_target):
            return {
                "status": "error",
                "message": (
                    "I parsed the same text for contact and message, so I stopped to avoid sending to the wrong person. "
                    "Please say: send 'your message' to contact on WhatsApp."
                ),
                "data": {"target": resolved_target, "message": resolved_message},
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
            _wait_for_whatsapp(timeout=12)
            _focus_and_prime_ui()
            return True
        except Exception as e:
            logger.error(f"[WhatsApp] open_app failed: {e}")
            return False

    def open_chat(self, target: str) -> bool:
        try:
            if _looks_like_phone_target(target):
                phone = _sanitize_phone(target).lstrip("+")
                _open_whatsapp_protocol(f"whatsapp://send?phone={phone}")
                _wait_for_whatsapp(timeout=WHATSAPP_BOOT_TIMEOUT)
                _focus_and_prime_ui()
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
