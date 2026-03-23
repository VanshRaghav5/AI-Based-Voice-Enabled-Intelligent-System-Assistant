"""Tests for Parameter Extractor."""
import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestParameterExtractor:
    """Test parameter extraction from commands."""
    
    def test_extractor_initialization(self):
        """Test parameter extractor can be initialized."""
        from backend.llm.parameter_extractor import ParameterExtractor
        extractor = ParameterExtractor()
        
        assert extractor is not None
        assert extractor.confidence_threshold == 0.7
    
    def test_extract_file_path(self):
        """Test extracting file path from command."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        params, confidence = parameter_extractor.extract(
            "open file C:/Users/test.txt",
            "file.open"
        )
        
        assert "path" in params
        assert "test.txt" in params["path"]
        assert confidence > 0.5
    
    def test_extract_whatsapp_message_and_contact(self):
        """Test extracting WhatsApp message and contact."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        params, confidence = parameter_extractor.extract(
            "send 'hello world' to John on WhatsApp",
            "whatsapp.send"
        )
        
        assert "message" in params
        assert "contact" in params
        assert params["message"] == "hello world"
        assert "john" in params["contact"].lower()
        assert confidence > 0.7
    
    def test_extract_email_parameters(self):
        """Test extracting email parameters."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        params, confidence = parameter_extractor.extract(
            "send email to user@example.com subject 'Test' body 'Hello'",
            "email.send"
        )
        
        assert "to" in params
        assert params["to"] == "user@example.com"
        assert "subject" in params
        assert "body" in params

    def test_extract_email_unquoted_subject_and_body(self):
        """Unquoted email subject/body should be extracted from natural phrasing."""
        from backend.llm.parameter_extractor import parameter_extractor

        params, confidence = parameter_extractor.extract(
            "send email to user@example.com subject sprint update body deployment completed",
            "email.send"
        )

        assert params.get("subject", "") == "sprint update"
        assert params.get("body", "") == "deployment completed"
        assert confidence >= 0.6
    
    def test_extract_volume_step(self):
        """Test extracting volume step parameter."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        params, confidence = parameter_extractor.extract(
            "volume up 15",
            "system.volume.up"
        )
        
        assert "step" in params
        assert params["step"] == 15
        assert confidence > 0.8
    
    def test_extract_browser_url(self):
        """Test extracting browser URL."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        params, confidence = parameter_extractor.extract(
            "open url google.com",
            "browser.open"
        )
        
        assert "url" in params
        assert "google.com" in params["url"]

    def test_extract_browser_url_without_url_keyword(self):
        """Natural phrasing like 'open github.com' should still extract URL."""
        from backend.llm.parameter_extractor import parameter_extractor

        params, confidence = parameter_extractor.extract(
            "open github.com/docs",
            "browser.open"
        )

        assert params.get("url", "").startswith("github.com")
        assert confidence >= 0.8
    
    def test_extract_search_query(self):
        """Test extracting search query."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        params, confidence = parameter_extractor.extract(
            "search for Python tutorials",
            "browser.search_google"
        )
        
        assert "query" in params
        assert "python" in params["query"].lower()

    def test_extract_multiword_search_query(self):
        """Multi-word search queries should not be truncated at first space."""
        from backend.llm.parameter_extractor import parameter_extractor

        params, confidence = parameter_extractor.extract(
            "search for python decorators tutorial",
            "browser.search_google"
        )

        assert params.get("query", "") == "python decorators tutorial"
        assert confidence >= 0.8

    def test_extract_lookup_style_search_query(self):
        """Lookup phrasing should map to a usable search query."""
        from backend.llm.parameter_extractor import parameter_extractor

        params, confidence = parameter_extractor.extract(
            "look up latest ai safety papers on google",
            "browser.search_google"
        )

        assert "ai safety" in params.get("query", "")
        assert confidence >= 0.8

    def test_extract_multiword_app_name(self):
        """App extraction should keep multi-word app names."""
        from backend.llm.parameter_extractor import parameter_extractor

        params, confidence = parameter_extractor.extract(
            "launch visual studio code",
            "app.launch"
        )

        assert params.get("app_name", "") == "visual studio code"
        assert confidence >= 0.8
    
    def test_extract_file_move_params(self):
        """Test extracting source and destination for file move."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        params, confidence = parameter_extractor.extract(
            "move file from C:/old.txt to C:/new.txt",
            "file.move"
        )
        
        assert "source" in params
        assert "destination" in params
        assert "old.txt" in params["source"]
        assert "new.txt" in params["destination"]
    
    def test_get_missing_parameters(self):
        """Test identifying missing parameters."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        # WhatsApp requires message and contact
        extracted = {"message": "hello"}
        missing = parameter_extractor.get_missing_parameters("whatsapp.send", extracted)
        
        assert "contact" in missing
        assert "message" not in missing
    
    def test_extract_unknown_tool_returns_low_confidence(self):
        """Test extracting for unknown tool returns low confidence."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        params, confidence = parameter_extractor.extract(
            "do something",
            "unknown.tool"
        )
        
        assert confidence < 0.7


class TestParameterExtractionEdgeCases:
    """Test edge cases in parameter extraction."""
    
    def test_extract_from_empty_command(self):
        """Test extraction from empty command."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        params, confidence = parameter_extractor.extract("", "file.open")
        
        assert params == {} or "path" not in params
        assert confidence < 0.5
    
    def test_extract_path_with_spaces(self):
        """Test extracting path with spaces."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        params, confidence = parameter_extractor.extract(
            'open file "C:/My Documents/test file.txt"',
            "file.open"
        )
        
        if "path" in params:
            assert "My Documents" in params["path"]
    
    def test_extract_multiple_numbers_picks_first(self):
        """Test volume extraction with multiple numbers."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        params, confidence = parameter_extractor.extract(
            "volume up 5 times by 10",
            "system.volume.up"
        )
        
        assert "step" in params
        # Should extract first number
        assert isinstance(params["step"], int)
    
    def test_extract_whatsapp_message_only(self):
        """Test extracting WhatsApp message without contact."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        params, confidence = parameter_extractor.extract(
            "send 'hello' on WhatsApp",
            "whatsapp.send"
        )
        
        assert "message" in params
        # Confidence should be lower without contact
        assert confidence < 0.9

    def test_extract_unquoted_whatsapp_message_and_contact(self):
        """Unquoted WhatsApp command should keep message/contact separated."""
        from backend.llm.parameter_extractor import parameter_extractor

        params, confidence = parameter_extractor.extract(
            "send testing to vansh on whatsapp",
            "whatsapp.send"
        )

        assert params.get("message", "").lower() == "testing"
        assert params.get("contact", "").lower() == "vansh"
        assert confidence >= 0.8
    
    def test_normalize_path_converts_slashes(self):
        """Test path normalization converts forward slashes."""
        from backend.llm.parameter_extractor import parameter_extractor
        
        # Extract path with forward slashes
        params, _ = parameter_extractor.extract(
            "open C:/Users/Test/file.txt",
            "file.open"
        )
        
        if "path" in params:
            # On Windows, should have backslashes
            assert "\\" in params["path"] or "/" in params["path"]
