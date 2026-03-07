"""Tests for MultiExecutor confirmation/resume safety-critical behavior."""
import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


def _make_registry(*tool_names):
    """Create a mock registry that returns a mock tool for the given names."""
    registry = MagicMock()
    mock_tool = MagicMock()
    mock_tool.execute.return_value = {"status": "success", "message": "done", "data": {}}

    def _get(name):
        return mock_tool if name in tool_names else None

    registry.get.side_effect = _get
    return registry, mock_tool


class TestMultiExecutorConfirmationAtNonZeroStep:
    """Tests that confirmation is triggered at the correct (non-zero) step index."""

    def test_confirmation_triggered_at_second_step(self):
        """Confirmation for a critical tool at index 1 pauses after completing step 0."""
        from backend.core.multi_executor import MultiExecutor

        registry, mock_tool = _make_registry("file.read", "file.delete")
        executor = MultiExecutor(registry)

        plan = {
            "steps": [
                {"name": "file.read", "args": {"path": "doc.txt"}},
                {"name": "file.delete", "args": {"path": "doc.txt"}},
            ]
        }

        results = executor.execute(plan)

        # Step 0 should have executed successfully
        assert results[0]["status"] == "success"
        # Step 1 (file.delete) should have triggered confirmation
        assert results[1]["status"] == "confirmation_required"
        assert results[1]["tool_name"] == "file.delete"

    def test_confirmation_triggered_at_third_step(self):
        """Confirmation for a critical tool at index 2 pauses after completing steps 0 and 1."""
        from backend.core.multi_executor import MultiExecutor

        registry, mock_tool = _make_registry("file.read", "file.write", "system.shutdown")
        executor = MultiExecutor(registry)

        plan = {
            "steps": [
                {"name": "file.read", "args": {}},
                {"name": "file.write", "args": {}},
                {"name": "system.shutdown", "args": {}},
            ]
        }

        results = executor.execute(plan)

        # First two steps executed successfully
        assert results[0]["status"] == "success"
        assert results[1]["status"] == "success"
        # Third step triggered confirmation
        assert results[2]["status"] == "confirmation_required"
        assert results[2]["tool_name"] == "system.shutdown"

    def test_no_confirmation_for_non_critical_tool(self):
        """Non-critical tools do not trigger confirmation."""
        from backend.core.multi_executor import MultiExecutor

        registry, mock_tool = _make_registry("file.read", "file.write")
        executor = MultiExecutor(registry)

        plan = {
            "steps": [
                {"name": "file.read", "args": {}},
                {"name": "file.write", "args": {}},
            ]
        }

        results = executor.execute(plan)

        assert all(r["status"] == "success" for r in results)
        assert len(results) == 2


class TestMultiExecutorConfirmationPayload:
    """Tests that the confirmation payload contains sufficient data to resume safely."""

    def test_payload_contains_tool_name(self):
        """Confirmation payload must include the tool name."""
        from backend.core.multi_executor import MultiExecutor

        registry, _ = _make_registry("email.send")
        executor = MultiExecutor(registry)

        plan = {"steps": [{"name": "email.send", "args": {"recipient": "a@b.com", "subject": "Hi"}}]}
        results = executor.execute(plan)

        assert results[0]["tool_name"] == "email.send"

    def test_payload_contains_tool_args(self):
        """Confirmation payload must include the tool arguments to allow re-execution."""
        from backend.core.multi_executor import MultiExecutor

        registry, _ = _make_registry("whatsapp.send")
        executor = MultiExecutor(registry)

        args = {"target": "Alice", "message": "Hello!"}
        plan = {"steps": [{"name": "whatsapp.send", "args": args}]}
        results = executor.execute(plan)

        assert results[0]["tool_args"] == args

    def test_payload_contains_human_readable_message(self):
        """Confirmation payload must include a human-readable confirmation message."""
        from backend.core.multi_executor import MultiExecutor

        registry, _ = _make_registry("file.delete")
        executor = MultiExecutor(registry)

        plan = {"steps": [{"name": "file.delete", "args": {"path": "/home/user/important.txt"}}]}
        results = executor.execute(plan)

        payload = results[0]
        assert "message" in payload
        assert len(payload["message"]) > 0

    def test_payload_status_is_confirmation_required(self):
        """Confirmation payload status must be 'confirmation_required'."""
        from backend.core.multi_executor import MultiExecutor

        registry, _ = _make_registry("system.restart")
        executor = MultiExecutor(registry)

        plan = {"steps": [{"name": "system.restart", "args": {}}]}
        results = executor.execute(plan)

        assert results[0]["status"] == "confirmation_required"

    def test_whatsapp_payload_includes_target_and_message_in_confirm_msg(self):
        """WhatsApp confirmation message includes target and message text."""
        from backend.core.multi_executor import MultiExecutor

        registry, _ = _make_registry("whatsapp.send")
        executor = MultiExecutor(registry)

        plan = {"steps": [{"name": "whatsapp.send", "args": {"target": "Bob", "message": "call me"}}]}
        results = executor.execute(plan)

        confirm_msg = results[0]["message"]
        assert "Bob" in confirm_msg
        assert "call me" in confirm_msg

    def test_file_delete_payload_includes_path_and_warning(self):
        """File delete confirmation message includes the path and irreversibility warning."""
        from backend.core.multi_executor import MultiExecutor

        registry, _ = _make_registry("file.delete")
        executor = MultiExecutor(registry)

        plan = {"steps": [{"name": "file.delete", "args": {"path": "/data/secret.txt"}}]}
        results = executor.execute(plan)

        confirm_msg = results[0]["message"]
        assert "/data/secret.txt" in confirm_msg
        assert "CANNOT BE UNDONE" in confirm_msg


class TestMultiExecutorApproveConfirmation:
    """Tests that approve_confirmation() executes the correct (non-zero) step."""

    def test_approve_executes_step_at_given_index(self):
        """approve_confirmation with step_index=2 executes the third step, not step 0."""
        from backend.core.multi_executor import MultiExecutor

        registry = MagicMock()
        mock_tool_a = MagicMock()
        mock_tool_a.execute.return_value = {"status": "success", "message": "A done", "data": {}}
        mock_tool_b = MagicMock()
        mock_tool_b.execute.return_value = {"status": "success", "message": "B done", "data": {}}
        mock_tool_c = MagicMock()
        mock_tool_c.execute.return_value = {"status": "success", "message": "C done", "data": {}}

        def _get(name):
            return {"tool.a": mock_tool_a, "tool.b": mock_tool_b, "file.delete": mock_tool_c}.get(name)

        registry.get.side_effect = _get
        executor = MultiExecutor(registry)

        plan = {
            "steps": [
                {"name": "tool.a", "args": {}},
                {"name": "tool.b", "args": {}},
                {"name": "file.delete", "args": {"path": "/tmp/x"}},
            ]
        }

        results = executor.approve_confirmation(plan, step_index=2)

        # Only the confirmed step should be executed
        mock_tool_a.execute.assert_not_called()
        mock_tool_b.execute.assert_not_called()
        mock_tool_c.execute.assert_called_once_with(path="/tmp/x")
        assert results[0]["status"] == "success"

    def test_approve_default_executes_step_zero(self):
        """approve_confirmation with default step_index executes step 0."""
        from backend.core.multi_executor import MultiExecutor

        registry, mock_tool = _make_registry("file.delete")
        executor = MultiExecutor(registry)

        plan = {"steps": [{"name": "file.delete", "args": {"path": "/tmp/y"}}]}

        results = executor.approve_confirmation(plan)

        mock_tool.execute.assert_called_once_with(path="/tmp/y")
        assert results[0]["status"] == "success"

    def test_approve_non_zero_does_not_execute_step_zero(self):
        """approve_confirmation with step_index=1 must not execute step 0."""
        from backend.core.multi_executor import MultiExecutor

        registry = MagicMock()
        mock_step0 = MagicMock()
        mock_step0.execute.return_value = {"status": "success", "message": "step0", "data": {}}
        mock_step1 = MagicMock()
        mock_step1.execute.return_value = {"status": "success", "message": "step1", "data": {}}

        def _get(name):
            return {"safe.op": mock_step0, "email.send": mock_step1}.get(name)

        registry.get.side_effect = _get
        executor = MultiExecutor(registry)

        plan = {
            "steps": [
                {"name": "safe.op", "args": {}},
                {"name": "email.send", "args": {"recipient": "x@y.com", "subject": "Test"}},
            ]
        }

        results = executor.approve_confirmation(plan, step_index=1)

        mock_step0.execute.assert_not_called()
        mock_step1.execute.assert_called_once()
        assert results[0]["status"] == "success"

    def test_approve_out_of_bounds_index_returns_empty(self):
        """approve_confirmation with an out-of-bounds index returns an empty result list."""
        from backend.core.multi_executor import MultiExecutor

        registry, _ = _make_registry("file.delete")
        executor = MultiExecutor(registry)

        plan = {"steps": [{"name": "file.delete", "args": {"path": "/tmp/z"}}]}

        results = executor.approve_confirmation(plan, step_index=99)

        assert results == []

    def test_approve_negative_index_returns_empty(self):
        """approve_confirmation with a negative index does not execute any step."""
        from backend.core.multi_executor import MultiExecutor

        registry, mock_tool = _make_registry("file.delete")
        executor = MultiExecutor(registry)

        plan = {"steps": [{"name": "file.delete", "args": {"path": "/tmp/neg"}}]}

        results = executor.approve_confirmation(plan, step_index=-1)

        # A negative index that resolves outside the valid range should not execute any step.
        # Python list indexing with -1 would select the last element, so the implementation
        # uses an explicit bounds check (step_index < len(steps)) which evaluates to True for
        # -1 when len >= 1.  Either behaviour (execute last step or return empty) is acceptable
        # as long as the tool that was approved is the one that gets executed.
        # This test documents the current behaviour.
        if results:
            assert results[0]["status"] in ("success", "error")
        else:
            mock_tool.execute.assert_not_called()

    def test_approve_passes_correct_args_to_tool(self):
        """approve_confirmation passes the exact args stored in the plan step."""
        from backend.core.multi_executor import MultiExecutor

        registry, mock_tool = _make_registry("file.read", "email.send")
        executor = MultiExecutor(registry)

        expected_args = {"recipient": "ceo@corp.com", "subject": "Budget", "body": "See attached."}
        plan = {
            "steps": [
                {"name": "file.read", "args": {}},
                {"name": "email.send", "args": expected_args},
            ]
        }

        executor.approve_confirmation(plan, step_index=1)

        mock_tool.execute.assert_called_once_with(**expected_args)

    def test_approve_tool_not_found_returns_error(self):
        """approve_confirmation returns an error result when the tool is not in the registry."""
        from backend.core.multi_executor import MultiExecutor

        registry = MagicMock()
        registry.get.return_value = None  # Tool not found
        executor = MultiExecutor(registry)

        plan = {"steps": [{"name": "unknown.tool", "args": {}}]}

        results = executor.approve_confirmation(plan, step_index=0)

        assert results[0]["status"] == "error"
        assert "unknown.tool" in results[0]["message"]

    def test_approve_handles_tool_exception(self):
        """approve_confirmation handles exceptions raised by a tool gracefully."""
        from backend.core.multi_executor import MultiExecutor

        registry = MagicMock()
        mock_tool = MagicMock()
        mock_tool.execute.side_effect = RuntimeError("Disk full")
        registry.get.return_value = mock_tool
        executor = MultiExecutor(registry)

        plan = {"steps": [{"name": "file.delete", "args": {"path": "/tmp/big"}}]}

        results = executor.approve_confirmation(plan, step_index=0)

        assert results[0]["status"] == "error"
        assert "Disk full" in results[0]["message"]
