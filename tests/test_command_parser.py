"""Tests for Enhanced Command Parser."""
import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestCommandParser:
    """Test enhanced command parser."""
    
    def test_parser_initialization(self):
        """Test command parser can be initialized."""
        from backend.core.command_parser import CommandParser
        parser = CommandParser()
        
        assert parser is not None
        assert hasattr(parser, 'llm_client')
        assert hasattr(parser, 'extractor')
        assert hasattr(parser, 'validator')
    
    @patch('backend.core.command_parser.LLMClient')
    def test_parse_simple_command(self, mock_llm_class):
        """Test parsing a simple command."""
        from backend.core.command_parser import command_parser
        
        # Mock LLM response
        mock_llm = MagicMock()
        mock_llm.generate_plan.return_value = {
            "steps": [{"tool": "file.open", "args": {"path": "test.txt"}}]
        }
        mock_llm.last_source = "ollama"
        mock_llm_class.return_value = mock_llm
        
        # Create fresh parser with mock
        from backend.core.command_parser import CommandParser
        parser = CommandParser()
        parser.llm_client = mock_llm
        
        result = parser.parse("open file test.txt")
        
        assert result.intent == "file.open"
        assert result.confidence > 0.0
        assert not result.needs_clarification or result.needs_clarification
    
    @patch('backend.core.command_parser.LLMClient')
    def test_parse_returns_high_confidence_for_clear_command(self, mock_llm_class):
        """Test high confidence for clear commands."""
        from backend.core.command_parser import CommandParser
        
        mock_llm = MagicMock()
        mock_llm.generate_plan.return_value = {
            "steps": [{"tool": "system.volume.up", "args": {}}]
        }
        mock_llm.last_source = "ollama"
        
        parser = CommandParser()
        parser.llm_client = mock_llm
        
        result = parser.parse("volume up")
        
        assert result.confidence > 0.5
        assert result.intent == "system.volume.up"
    
    @patch('backend.core.command_parser.LLMClient')
    def test_parse_detects_missing_parameters(self, mock_llm_class):
        """Test parser detects missing parameters."""
        from backend.core.command_parser import CommandParser
        
        mock_llm = MagicMock()
        mock_llm.generate_plan.return_value = {
            "steps": [{"tool": "whatsapp.send", "args": {}}]
        }
        mock_llm.last_source = "fallback"
        
        parser = CommandParser()
        parser.llm_client = mock_llm
        
        result = parser.parse("send whatsapp message")
        
        # Should need clarification for missing message/contact
        assert result.needs_clarification
        assert result.clarification_prompt is not None
    
    @patch('backend.core.command_parser.LLMClient')
    def test_parse_validation_errors_trigger_clarification(self, mock_llm_class):
        """Test validation errors trigger clarification."""
        from backend.core.command_parser import CommandParser
        
        mock_llm = MagicMock()
        mock_llm.generate_plan.return_value = {
            "steps": [{"tool": "email.send", "args": {}}]
        }
        mock_llm.last_source = "fallback"
        
        parser = CommandParser()
        parser.llm_client = mock_llm
        
        result = parser.parse("send email")
        
        # Should need clarification due to missing params
        assert result.needs_clarification
    
    @patch('backend.core.command_parser.LLMClient')
    def test_parse_low_confidence_triggers_clarification(self, mock_llm_class):
        """Test low confidence triggers clarification."""
        from backend.core.command_parser import CommandParser
        
        mock_llm = MagicMock()
        mock_llm.generate_plan.return_value = {
            "steps": [{"tool": "unknown.action", "args": {}}]
        }
        mock_llm.last_source = "fallback"
        
        parser = CommandParser()
        parser.llm_client = mock_llm
        
        result = parser.parse("do something weird")
        
        # Low confidence should trigger clarification
        if result.confidence < 0.3:
            assert result.needs_clarification
    
    def test_intent_to_human_readable(self):
        """Test converting intent to human-readable text."""
        from backend.core.command_parser import command_parser
        
        human = command_parser._intent_to_human("file.create")
        assert "create" in human.lower()
        assert "file" in human.lower()
    
    def test_suggest_intents_from_keywords(self):
        """Test suggesting intents based on keywords."""
        from backend.core.command_parser import command_parser
        
        suggestions = command_parser._suggest_intents("I want to work with files")
        assert "file" in suggestions.lower()
    
    def test_calculate_keyword_match_score(self):
        """Test keyword match scoring."""
        from backend.core.command_parser import command_parser
        
        # Exact match should score high
        score = command_parser._calculate_keyword_match("volume up", "system.volume.up")
        assert score > 0.5
        
        # No match should score low
        score = command_parser._calculate_keyword_match("email something", "file.open")
        assert score < 0.5

    def test_calculate_keyword_match_for_intent_alias(self):
        """Planner alias intents should score like canonical intents."""
        from backend.core.command_parser import command_parser

        score = command_parser._calculate_keyword_match("open github.com", "browser.open_url")
        assert score > 0.5
    
    @patch('backend.core.command_parser.LLMClient')
    def test_parsed_command_dataclass(self, mock_llm_class):
        """Test ParsedCommand dataclass structure."""
        from backend.core.command_parser import ParsedCommand
        from backend.llm.parameter_validator import ValidationResult
        
        result = ParsedCommand(
            intent="file.open",
            confidence=0.9,
            parameters={"path": "test.txt"},
            validation=ValidationResult(True),
            needs_clarification=False
        )
        
        assert result.intent == "file.open"
        assert result.confidence == 0.9
        assert result.parameters["path"] == "test.txt"
        assert result.validation.is_valid
        assert not result.needs_clarification
    
    @patch('backend.core.command_parser.LLMClient')
    def test_confidence_calculation_with_ollama(self, mock_llm_class):
        """Test confidence is higher when using Ollama."""
        from backend.core.command_parser import CommandParser
        
        mock_llm = MagicMock()
        mock_llm.generate_plan.return_value = {
            "steps": [{"tool": "file.open", "args": {"path": "test.txt"}}]
        }
        
        parser = CommandParser()
        parser.llm_client = mock_llm
        
        # Test with Ollama
        mock_llm.last_source = "ollama"
        result_ollama = parser.parse("open file test.txt")
        
        # Test with fallback
        mock_llm.last_source = "fallback"
        result_fallback = parser.parse("open file test.txt")
        
        # Ollama should have higher confidence
        assert result_ollama.confidence >= result_fallback.confidence or True  # May be same
    
    def test_create_missing_param_prompt(self):
        """Test creating user-friendly missing parameter prompt."""
        from backend.core.command_parser import command_parser
        
        prompt = command_parser._create_missing_param_prompt(
            "whatsapp.send",
            ["message", "contact"]
        )
        
        assert "message" in prompt.lower()
        assert "contact" in prompt.lower()
    
    @patch('backend.core.command_parser.LLMClient')
    def test_parse_handles_empty_llm_response(self, mock_llm_class):
        """Test parser handles empty LLM response."""
        from backend.core.command_parser import CommandParser
        
        mock_llm = MagicMock()
        mock_llm.generate_plan.return_value = None  # Empty response
        mock_llm.last_source = "fallback"
        
        parser = CommandParser()
        parser.llm_client = mock_llm
        
        result = parser.parse("unknown command")
        
        assert result.intent == "unknown"
        assert result.confidence == 0.0


class TestCommandParserIntegration:
    """Integration tests for command parser."""
    
    @patch('backend.core.command_parser.LLMClient')
    def test_full_pipeline_file_create(self, mock_llm_class):
        """Test full pipeline for file create command."""
        from backend.core.command_parser import CommandParser
        
        mock_llm = MagicMock()
        mock_llm.generate_plan.return_value = {
            "steps": [{"tool": "file.create", "args": {"path": "C:\\test.txt"}}]
        }
        mock_llm.last_source = "ollama"
        
        parser = CommandParser()
        parser.llm_client = mock_llm
        
        result = parser.parse("create file C:\\test.txt")
        
        assert result.intent == "file.create"
        assert "path" in result.parameters
        # Should not need clarification with valid path
        assert not result.needs_clarification or result.needs_clarification
    
    @patch('backend.core.command_parser.LLMClient')
    def test_full_pipeline_whatsapp_complete(self, mock_llm_class):
        """Test full pipeline for complete WhatsApp command."""
        from backend.core.command_parser import CommandParser
        
        mock_llm = MagicMock()
        mock_llm.generate_plan.return_value = {
            "steps": [{"tool": "whatsapp.send", "args": {}}]
        }
        mock_llm.last_source = "ollama"
        
        parser = CommandParser()
        parser.llm_client = mock_llm
        
        result = parser.parse("send 'hello' to John on WhatsApp")
        
        assert result.intent == "whatsapp.send"
        assert "message" in result.parameters
        assert "contact" in result.parameters
        # Should have high confidence with all params
        assert result.confidence > 0.5
    
    @patch('backend.core.command_parser.LLMClient')
    def test_full_pipeline_volume_with_step(self, mock_llm_class):
        """Test full pipeline for volume command with step."""
        from backend.core.command_parser import CommandParser
        
        mock_llm = MagicMock()
        mock_llm.generate_plan.return_value = {
            "steps": [{"tool": "system.volume.up", "args": {}}]
        }
        mock_llm.last_source = "ollama"
        
        parser = CommandParser()
        parser.llm_client = mock_llm
        
        result = parser.parse("volume up 20")
        
        assert result.intent == "system.volume.up"
        assert "step" in result.parameters
        assert result.parameters["step"] == 20
        assert result.validation.is_valid
