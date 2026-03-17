"""Tests for Intent Parser and LLM Client."""
import pytest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestLLMClient:
    """Test cases for LLM Client."""
    
    def test_llm_client_initialization(self):
        """Test LLM client can be initialized."""
        # Act
        from backend.llm.llm_client import LLMClient
        client = LLMClient(model="test-model")
        
        # Assert
        assert client is not None
        assert client.model == "test-model"
    
    @patch('backend.llm.llm_client.subprocess.run')
    def test_ollama_availability_check(self, mock_run):
        """Test Ollama availability detection."""
        # Arrange
        mock_run.return_value = MagicMock(returncode=0, stdout="ollama version 0.1.0")
        
        # Act
        from backend.llm.llm_client import LLMClient
        client = LLMClient()
        
        # Assert
        assert hasattr(client, 'ollama_available')
    
    def test_fallback_plan_generation_file_operations(self):
        """Test fallback plan generation for file operations."""
        # Arrange
        from backend.llm.llm_client import LLMClient
        client = LLMClient()
        
        # Act
        plan = client._create_fallback_plan("create file test.txt")
        
        # Assert
        assert plan is not None
        assert "steps" in plan
        assert len(plan["steps"]) > 0
        assert any("file" in step.get("tool", "") for step in plan["steps"])
    
    def test_fallback_plan_generation_whatsapp(self):
        """Test fallback plan generation for WhatsApp commands."""
        # Arrange
        from backend.llm.llm_client import LLMClient
        client = LLMClient()
        
        # Act
        plan = client._create_fallback_plan("send hello to John on WhatsApp")
        
        # Assert
        assert plan is not None
        assert "steps" in plan
        assert any("whatsapp" in step.get("tool", "") for step in plan["steps"])
    
    def test_fallback_plan_generation_system_commands(self):
        """Test fallback plan generation for system commands."""
        # Arrange
        from backend.llm.llm_client import LLMClient
        client = LLMClient()
        
        # Act
        plan = client._create_fallback_plan("increase volume")
        
        # Assert
        assert plan is not None
        assert "steps" in plan
        assert any("volume" in step.get("tool", "") for step in plan["steps"])
    
    @patch('backend.llm.llm_client.subprocess.run')
    def test_generate_plan_with_ollama(self, mock_run):
        """Test plan generation using Ollama."""
        # Arrange
        mock_plan = {"steps": [{"tool": "file.open", "args": {"path": "test.txt"}}]}
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_plan)
        )
        
        # Act
        from backend.llm.llm_client import LLMClient
        client = LLMClient()
        client.ollama_available = True
        plan = client.generate_plan("open file test.txt")
        
        # Assert
        assert plan is not None
        assert "steps" in plan
    
    @patch('backend.llm.llm_client.subprocess.run')
    def test_generate_plan_fallback_on_ollama_failure(self, mock_run):
        """Test fallback to keyword matching when Ollama fails."""
        # Arrange
        mock_run.return_value = MagicMock(returncode=1, stderr="Error")
        
        # Act
        from backend.llm.llm_client import LLMClient
        client = LLMClient()
        plan = client.generate_plan("volume up")
        
        # Assert
        assert plan is not None
        assert "steps" in plan
    
    def test_fallback_handles_unknown_command(self):
        """Test fallback returns None for unknown commands."""
        # Arrange
        from backend.llm.llm_client import LLMClient
        client = LLMClient()
        
        # Act
        plan = client._create_fallback_plan("xyzzy abracadabra nonsense")
        
        # Assert
        assert plan is None or len(plan.get("steps", [])) == 0

    def test_fallback_understands_polite_open_youtube_phrase(self):
        """Fallback should handle conversational phrasing, not only strict templates."""
        from backend.llm.llm_client import LLMClient
        client = LLMClient()

        plan = client._create_fallback_plan("could you please open youtube for me")

        assert plan is not None
        assert "steps" in plan
        assert plan["steps"][0].get("name") == "browser.open_youtube"

    def test_fallback_uses_user_command_from_wrapped_prompt(self):
        """Fallback should parse USER COMMAND payload even when prompt includes context wrappers."""
        from backend.llm.llm_client import LLMClient
        client = LLMClient()

        wrapped = (
            "MEMORY CONTEXT:\n"
            "- last_file_path: None\n"
            "USER COMMAND: please increase the volume\n"
            "REPLAN ITERATION: 2"
        )
        plan = client._create_fallback_plan(wrapped)

        assert plan is not None
        assert "steps" in plan
        assert plan["steps"][0].get("name") == "system.volume.up"

    def test_generate_plan_falls_back_when_ollama_plan_has_no_steps(self):
        """If Ollama returns JSON without executable steps, client should fallback to keyword parsing."""
        from backend.llm.llm_client import LLMClient
        client = LLMClient()

        client.ollama_available = True
        client.session = MagicMock()
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {"response": "{\"status\":\"ok\"}"}
        client.session.post.return_value = fake_response

        plan = client.generate_plan("open youtube")

        assert plan is not None
        assert "steps" in plan
        assert plan["steps"][0].get("name") == "browser.open_youtube"

    def test_fallback_generates_multistep_youtube_on_chrome_command(self):
        """Fallback should emit chained app+search steps for advanced browser requests."""
        from backend.llm.llm_client import LLMClient
        client = LLMClient()

        plan = client._create_fallback_plan("can you search youtube on chrome and open Mr beast on youtube")

        assert plan is not None
        assert "steps" in plan
        assert len(plan["steps"]) >= 2
        assert plan["steps"][0].get("name") == "app.open"
        assert plan["steps"][0].get("args", {}).get("app_name") == "chrome"
        assert plan["steps"][1].get("name") == "browser.open_url"
        assert "youtube.com/results?search_query=" in plan["steps"][1].get("args", {}).get("url", "")

    def test_fallback_routes_latest_video_request_to_latest_video_tool(self):
        """Latest/newest video intents should open a video directly, not only search results."""
        from backend.llm.llm_client import LLMClient
        client = LLMClient()

        plan = client._create_fallback_plan("open youtube and search mr beast and open his latest video")

        assert plan is not None
        assert "steps" in plan
        assert any(step.get("name") == "browser.open_youtube_latest_video" for step in plan["steps"])


class TestIntentParsing:
    """Test intent parsing and entity extraction."""
    
    def test_parse_file_path_from_command(self):
        """Test extracting file path from commands."""
        # Arrange
        from backend.llm.llm_client import LLMClient
        client = LLMClient()
        
        # Act
        plan = client._create_fallback_plan("open file C:/Users/test.txt")
        
        # Assert
        assert plan is not None
        if plan and "steps" in plan and len(plan["steps"]) > 0:
            args = plan["steps"][0].get("args", {})
            assert "path" in args or "C:/Users/test.txt" in str(plan)
    
    def test_parse_whatsapp_message_and_target(self):
        """Test extracting WhatsApp message and target."""
        # Arrange
        from backend.llm.llm_client import LLMClient
        client = LLMClient()
        
        # Act
        plan = client._create_fallback_plan("send hello world to Sarah on WhatsApp")
        
        # Assert
        assert plan is not None
        if plan and "steps" in plan and len(plan["steps"]) > 0:
            args = plan["steps"][0].get("args", {})
            # Should extract message and target
            assert len(args) > 0
    
    def test_parse_volume_step_amount(self):
        """Test extracting volume step amount."""
        # Arrange
        from backend.llm.llm_client import LLMClient
        client = LLMClient()
        
        # Act
        plan = client._create_fallback_plan("volume up 10")
        
        # Assert
        assert plan is not None
        if plan and "steps" in plan and len(plan["steps"]) > 0:
            args = plan["steps"][0].get("args", {})
            # Should have step parameter
            assert "step" in args or args == {}
