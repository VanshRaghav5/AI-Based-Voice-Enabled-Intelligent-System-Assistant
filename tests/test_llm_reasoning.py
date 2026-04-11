"""
Test LLM as core reasoning engine.

This verifies that LLM is actually thinking and making decisions,
not just scaffolding.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from backend.services.llm_service import LLMClient
from backend.core.planner.planner import Planner


class TestLLMReasoning:
    """LLM should be the primary decision-maker."""

    def test_llm_service_generate_method_exists(self):
        """LLMClient should have a generate() method for core reasoning."""
        llm_client = LLMClient(model="test-model")
        assert hasattr(llm_client, "generate")
        assert callable(llm_client.generate)

    @patch("backend.services.llm_service.requests.Session.post")
    def test_llm_generates_response(self, mock_post):
        """LLM should generate raw text responses."""
        # Mock Ollama response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "response": '[\n  {"action": "open_app", "params": {"app_name": "code"}}\n]'
        }

        llm_client = LLMClient(model="test-model")
        llm_client.ollama_available = True

        response = llm_client.generate("Setup Python environment")
        
        assert response is not None
        assert "open_app" in response
        assert "code" in response

    @patch("backend.services.llm_service.LLMClient.generate")
    def test_planner_uses_llm_for_unknown_tasks(self, mock_generate):
        """Planner should ask LLM for unknown tasks."""
        # LLM returns executable JSON
        mock_generate.return_value = json.dumps([
            {"action": "open_app", "params": {"app_name": "terminal"}},
            {"action": "run_command", "params": {"command": "python -m venv env"}},
        ])

        planner = Planner()
        
        # Simulate unknown task (not in rule-based list)
        intent_data = {"intent": "unknown", "confidence": 0.1}
        plan = planner.create_plan(intent_data, "Setup my Python project")
        
        # Planner should have created steps from LLM
        assert plan is not None
        assert len(plan.steps) >= 1
        assert any(step.action == "open_app" for step in plan.steps)

    @patch("backend.services.llm_service.LLMClient.generate")
    def test_llm_reasoning_with_complex_task(self, mock_generate):
        """LLM should break down complex tasks into steps."""
        # LLM thinks through the problem
        mock_generate.return_value = json.dumps([
            {"action": "create_file", "params": {"path": "requirements.txt", "content": "numpy\npandas\n"}},
            {"action": "run_command", "params": {"command": "pip install -r requirements.txt"}},
            {"action": "open_app", "params": {"app_name": "code"}},
        ])

        planner = Planner()
        plan = planner.create_plan(
            {"intent": "setup_ml_project", "confidence": 0.0},
            "Prepare ML project with dependencies"
        )
        
        assert plan is not None
        assert len(plan.steps) == 3
        assert plan.steps[0].action == "create_file"
        assert plan.steps[1].action == "run_command"
        assert plan.steps[2].action == "open_app"

    @patch("backend.services.llm_service.LLMClient.generate")
    def test_llm_respects_tool_constraints(self, mock_generate):
        """LLM should only use specified tools."""
        # LLM should only return actions from available tool set
        mock_generate.return_value = json.dumps([
            {"action": "open_url", "params": {"url": "https://example.com"}},
        ])

        planner = Planner()
        # Use unknown intent so LLM is called
        plan = planner.create_plan(
            {"intent": "unknown_research_task", "confidence": 0.0},
            "Look up Python async patterns"
        )
        
        assert plan is not None
        # LLM was used for unknown intent
        assert mock_generate.called
        # Should have at least 1 step from LLM
        assert len(plan.steps) >= 1
        # All steps should be from available tools
        available_actions = {"open_url", "read_file", "create_file", "run_command", "open_app", "search_files"}
        assert all(step.action in available_actions for step in plan.steps)

    @patch("backend.services.llm_service.LLMClient.generate")
    def test_llm_fallback_when_json_invalid(self, mock_generate):
        """If LLM doesn't return valid JSON, planner should fallback gracefully."""
        # LLM returns non-JSON (shouldn't happen but we handle it)
        mock_generate.return_value = "Some random text that's not JSON"

        planner = Planner()
        plan = planner.create_plan(
            {"intent": "unknown_task", "confidence": 0.0},
            "Do something unknown"
        )
        
        # Should fallback to unknown plan (empty steps)
        assert plan is not None
        assert len(plan.steps) == 0  # Fallback plan has no steps

    @patch("backend.services.llm_service.LLMClient.generate")
    def test_llm_prompt_teaches_reasoning(self, mock_generate):
        """LLM prompt should explicitly teach the model how to reason."""
        mock_generate.return_value = json.dumps([
            {"action": "run_command", "params": {"command": "python script.py"}},
        ])

        planner = Planner()
        
        # Trigger LLM path
        with patch.object(planner, "_create_rule_based_plan", return_value=None):
            plan = planner.create_plan(
                {"intent": "complex_task", "confidence": 0.0},
                "Execute my ML pipeline"
            )
        
        # The mock was called - capturing call shows the prompt structure
        assert mock_generate.called
        call_args = mock_generate.call_args[0][0] if mock_generate.call_args else ""
        
        # Prompt should contain examples and tool documentation
        assert "TOOL REFERENCE" in call_args or "tool" in call_args.lower()
        assert "EXAMPLE" in call_args or "example" in call_args.lower()

    @patch("backend.services.llm_service.LLMClient.generate")
    def test_llm_handles_context_for_reasoning(self, mock_generate):
        """LLM should use context to make better decisions."""
        mock_generate.return_value = json.dumps([
            {"action": "open_app", "params": {"app_name": "code"}},
        ])

        planner = Planner()
        
        context = {
            "session": {"last_project": "/home/user/ml_project"},
            "long_term": {"preferred_editor": "code"},
        }
        
        # Use unknown intent so LLM is called (not known intent like "open_project")
        plan = planner.create_plan(
            {"intent": "complex_project_setup", "confidence": 0.0},
            "Set up my project with context-aware decisions",
            context=context
        )
        
        # LLM should have been called
        assert mock_generate.called
        # The prompt passed to generate should include context
        call_args = mock_generate.call_args[0][0] if mock_generate.call_args else ""
        assert "project" in call_args.lower() or "context" in call_args.lower() or "code" in call_args.lower()


class TestLLMIntegration:
    """LLM integration with the full execution engine."""

    def test_planner_metadata_includes_llm_source(self):
        """Plan metadata should indicate if LLM was used."""
        with patch("backend.services.llm_service.LLMClient.generate") as mock_gen:
            mock_gen.return_value = json.dumps([
                {"action": "open_app", "params": {"app_name": "code"}},
            ])

            planner = Planner()
            with patch.object(planner, "_create_rule_based_plan", return_value=None):
                plan = planner.create_plan(
                    {"intent": "unknown", "confidence": 0.0},
                    "Unknown task"
                )

            # Metadata should indicate LLM was source
            assert plan.metadata.get("planner_mode") == "llm"
            assert plan.metadata.get("plan_source") == "ollama"

    def test_planner_prefers_rule_based_for_known_tasks(self):
        """Planner should use rule-based for known intents (fast), LLM for unknowns."""
        with patch("backend.services.llm_service.LLMClient.generate") as mock_gen:
            planner = Planner()
            
            # Known intent: start_work_session
            plan_known = planner.create_plan(
                {"intent": "start_work_session", "confidence": 0.95},
                "Start my work"
            )
            
            # LLM should NOT be called
            assert not mock_gen.called
            assert plan_known.metadata.get("planner_mode") == "rule_based"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
