"""Regression tests for WhatsApp desktop automation flow."""

import os
import sys
from unittest.mock import patch

import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


class TestWhatsAppDesktopKeyFlow:
    """Validate WhatsApp key and click sequencing."""

    def test_contact_search_variants_do_not_include_quotes(self):
        from backend.automation import whatsapp_desktop as wd

        variants = wd._contact_search_variants("Vansh")
        assert variants
        assert all('"' not in value and "'" not in value for value in variants)

    def test_open_chat_by_contact_uses_new_chat_keyboard_flow(self):
        from backend.automation import whatsapp_desktop as wd

        with patch("backend.automation.whatsapp_desktop._focus_and_prime_ui"):
            with patch("backend.automation.whatsapp_desktop._search_contact_in_new_chat") as mock_new_chat:
                with patch("backend.automation.whatsapp_desktop._search_contact") as mock_sidebar_search:
                    with patch("backend.automation.whatsapp_desktop._open_first_result_with_keyboard") as mock_kb:
                        with patch("backend.automation.whatsapp_desktop._press_key") as mock_press:
                            with patch("backend.automation.whatsapp_desktop._focus_whatsapp"):
                                with patch("backend.automation.whatsapp_desktop._sleep"):
                                    wd._open_chat_by_contact("Vansh Raghav")

        mock_new_chat.assert_called_once_with("Vansh Raghav")
        mock_sidebar_search.assert_not_called()
        mock_kb.assert_not_called()
        assert all(call.args != ("down",) for call in mock_press.call_args_list)
        assert any(call.args == ("enter",) for call in mock_press.call_args_list)

    def test_open_chat_by_contact_uses_short_name_variants(self):
        from backend.automation import whatsapp_desktop as wd

        with patch("backend.automation.whatsapp_desktop._focus_and_prime_ui"):
            with patch("backend.automation.whatsapp_desktop._search_contact_in_new_chat") as mock_new_chat:
                with patch("backend.automation.whatsapp_desktop._press_key"):
                    with patch("backend.automation.whatsapp_desktop._focus_whatsapp"):
                        with patch("backend.automation.whatsapp_desktop._sleep"):
                            wd._open_chat_by_contact("Vansh")

        assert mock_new_chat.call_count >= 1
        first_variant = mock_new_chat.call_args_list[0].args[0]
        assert "vansh" in first_variant.lower()

    def test_search_contact_in_new_chat_opens_picker_and_types_contact(self):
        from backend.automation import whatsapp_desktop as wd

        with patch("backend.automation.whatsapp_desktop._open_new_chat_dialog") as mock_open:
            with patch("backend.automation.whatsapp_desktop._clear_search_box") as mock_clear:
                with patch("backend.automation.whatsapp_desktop._paste_text") as mock_paste:
                    with patch("backend.automation.whatsapp_desktop._sleep"):
                        wd._search_contact_in_new_chat("Vansh")

        mock_open.assert_called_once()
        mock_clear.assert_called_once()
        mock_paste.assert_called_once_with("Vansh")

    def test_open_chat_by_contact_requires_non_empty_contact(self):
        from backend.automation.error_handler import AutomationError
        from backend.automation import whatsapp_desktop as wd

        with pytest.raises(AutomationError):
            wd._open_chat_by_contact("   ")

    def test_send_message_targets_composer_and_sends(self):
        from backend.automation import whatsapp_desktop as wd

        with patch("backend.automation.whatsapp_desktop._focus_whatsapp") as mock_focus_window:
            with patch("backend.automation.whatsapp_desktop._focus_message_composer") as mock_focus:
                with patch("backend.automation.whatsapp_desktop._paste_text") as mock_paste:
                    with patch("backend.automation.whatsapp_desktop._press_key") as mock_press:
                        with patch("backend.automation.whatsapp_desktop._sleep"):
                            wd._send_message_in_active_chat("hello")

        mock_focus_window.assert_called_once()
        mock_focus.assert_called_once()
        mock_paste.assert_called_once_with("hello")
        assert any(call.args == ("enter",) for call in mock_press.call_args_list)


class TestAutomationRouterWhatsApp:
    """Validate router behavior for WhatsApp intents."""

    def test_send_whatsapp_returns_error_when_send_fails(self):
        from backend.automation import automation_router as router

        with patch.object(router.whatsapp, "open_app") as mock_open_app:
            with patch.object(router.whatsapp, "send_message", return_value=False):
                result = router.execute(
                    {"intent": "send_whatsapp", "target": "John", "data": "Hello"}
                )

        assert result["status"] == "error"
        assert "Failed to send" in result["message"]
        mock_open_app.assert_not_called()

    def test_open_whatsapp_chat_returns_error_when_open_chat_fails(self):
        from backend.automation import automation_router as router

        with patch.object(router.whatsapp, "open_app") as mock_open_app:
            with patch.object(router.whatsapp, "open_chat", return_value=False):
                result = router.execute(
                    {"intent": "open_whatsapp_chat", "target": "John"}
                )

        assert result["status"] == "error"
        assert "Could not open chat" in result["message"]
        mock_open_app.assert_not_called()


class TestWhatsAppSendToolSafety:
    def test_send_tool_blocks_when_message_matches_target(self):
        from backend.automation.whatsapp_desktop import WhatsAppSendTool

        tool = WhatsAppSendTool()
        result = tool.execute(target="Vansh", message="Vansh")

        assert result["status"] == "error"
        assert "same text for contact and message" in result["message"]

    def test_message_normalization_removes_target_suffix(self):
        from backend.automation.whatsapp_desktop import _normalize_message_for_target

        normalized = _normalize_message_for_target("testing to swayam gla", "swayam gla")
        assert normalized == "testing"

    def test_message_normalization_removes_full_command_residue(self):
        from backend.automation.whatsapp_desktop import _normalize_message_for_target

        normalized = _normalize_message_for_target(
            "send message testing to swayam gla on whatsapp",
            "swayam gla",
        )
        assert normalized == "testing"
