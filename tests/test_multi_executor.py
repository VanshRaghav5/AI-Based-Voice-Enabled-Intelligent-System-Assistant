"""Tests for MultiExecutor confirmation and resume behavior."""
import pytest
from unittest.mock import MagicMock
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _make_registry(tool_name="file.delete", tool_result=None):
    """Helper: build a mock ToolRegistry with one registered tool."""
    registry = MagicMock()
    mock_tool = MagicMock()
    mock_tool.execute.return_value = tool_result or {
        "status": "success",
        "message": "Done",
        "data": {}
    }
    registry.get.side_effect = lambda name: mock_tool if name == tool_name else None
    return registry, mock_tool


class TestMultiExecutorConfirmation:
    """Tests for confirmation/resume behavior in MultiExecutor."""

    def test_confirmation_triggered_on_non_zero_step_index(self):
        """Confirmation on a critical step that is NOT the first step includes correct step_index."""
        from backend.core.multi_executor import MultiExecutor

        registry, _ = _make_registry("file.delete")
        executor = MultiExecutor(registry)

        plan = {
            "steps": [
                {"name": "app.open", "args": {"name": "notepad"}},   # step 0 – safe
                {"name": "file.delete", "args": {"path": "/tmp/x"}}, # step 1 – critical
            ]
        }

        # Provide a mock tool for the safe step so it succeeds
        safe_tool = MagicMock()
        safe_tool.execute.return_value = {"status": "success", "message": "opened", "data": {}}
        registry.get.side_effect = lambda name: (
            safe_tool if name == "app.open" else
            MagicMock() if name == "file.delete" else None
        )

        results = executor.execute(plan)

        confirmation = results[-1]
        assert confirmation["status"] == "confirmation_required"
        assert confirmation["step_index"] == 1, (
            f"Expected step_index=1 for the second step, got {confirmation['step_index']}"
        )

    def test_confirmation_payload_contains_required_resume_data(self):
        """Confirmation payload includes tool_name, tool_args, and step_index."""
        from backend.core.multi_executor import MultiExecutor

        registry, _ = _make_registry("system.shutdown")
        executor = MultiExecutor(registry)

        plan = {
            "steps": [
                {"name": "system.shutdown", "args": {}},
            ]
        }

        results = executor.execute(plan)

        assert len(results) == 1
        payload = results[0]
        assert payload["status"] == "confirmation_required"
        assert "step_index" in payload
        assert "tool_name" in payload
        assert "tool_args" in payload

    def test_approve_confirmation_executes_correct_step(self):
        """approve_confirmation executes the step at the correct step_index, not always step 0."""
        from backend.core.multi_executor import MultiExecutor

        registry = MagicMock()

        safe_tool = MagicMock()
        safe_tool.execute.return_value = {"status": "success", "message": "ok", "data": {}}

        delete_tool = MagicMock()
        delete_tool.execute.return_value = {"status": "success", "message": "deleted", "data": {}}

        registry.get.side_effect = lambda name: (
            safe_tool if name == "app.open" else
            delete_tool if name == "file.delete" else None
        )

        executor = MultiExecutor(registry)

        plan = {
            "steps": [
                {"name": "app.open", "args": {"name": "notepad"}},   # step 0
                {"name": "file.delete", "args": {"path": "/tmp/y"}}, # step 1 – critical
            ]
        }

        # Trigger confirmation; safe step (0) executes normally, critical step (1) pauses
        results = executor.execute(plan)
        confirmation = results[-1]
        assert confirmation["status"] == "confirmation_required"
        step_index = confirmation["step_index"]
        assert step_index == 1

        # safe_tool was called once (during initial execute) – reset to isolate approval
        safe_tool.execute.reset_mock()

        # Now approve
        approval_results = executor.approve_confirmation(plan, step_index)

        assert len(approval_results) == 1
        assert approval_results[0]["status"] == "success"

        # During approval only the critical step (1) should run
        delete_tool.execute.assert_called_once_with(path="/tmp/y")
        safe_tool.execute.assert_not_called()

    def test_approve_confirmation_defaults_to_step_zero(self):
        """approve_confirmation with step_index=0 executes the first step."""
        from backend.core.multi_executor import MultiExecutor

        registry, mock_tool = _make_registry("system.restart")
        executor = MultiExecutor(registry)

        plan = {
            "steps": [
                {"name": "system.restart", "args": {}},
            ]
        }

        results = executor.approve_confirmation(plan, step_index=0)

        assert len(results) == 1
        assert results[0]["status"] == "success"
        mock_tool.execute.assert_called_once()
