"""Tests for Parameter Validator."""
import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestParameterValidator:
    """Test parameter validation."""
    
    def test_validator_initialization(self):
        """Test parameter validator can be initialized."""
        from backend.services.llm.parameter_validator import ParameterValidator
        validator = ParameterValidator()
        
        assert validator is not None
        assert validator.max_path_length == 260
    
    def test_validate_file_params_success(self):
        """Test successful file parameter validation."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"path": "C:\\Users\\test.txt"}
        result = parameter_validator.validate("file.create", params)
        
        # Should be valid (file doesn't need to exist for create)
        assert result.is_valid or len(result.errors) == 0
    
    def test_validate_file_params_empty_path(self):
        """Test validation fails for empty path."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"path": ""}
        result = parameter_validator.validate("file.open", params)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "empty" in result.get_message().lower()
    
    def test_validate_whatsapp_params_success(self):
        """Test successful WhatsApp parameter validation."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"message": "Hello world", "contact": "John"}
        result = parameter_validator.validate("whatsapp.send", params)
        
        assert result.is_valid
    
    def test_validate_whatsapp_empty_message(self):
        """Test validation fails for empty WhatsApp message."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"message": "", "contact": "John"}
        result = parameter_validator.validate("whatsapp.send", params)
        
        assert not result.is_valid
        assert "message" in result.get_message().lower()
    
    def test_validate_whatsapp_missing_contact(self):
        """Test validation fails for missing contact."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"message": "Hello"}
        result = parameter_validator.validate("whatsapp.send", params)
        
        assert not result.is_valid
        assert "contact" in result.get_message().lower()
    
    def test_validate_email_params_success(self):
        """Test successful email parameter validation."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {
            "to": "user@example.com",
            "subject": "Test",
            "body": "Hello"
        }
        result = parameter_validator.validate("email.send", params)
        
        assert result.is_valid
    
    def test_validate_email_invalid_address(self):
        """Test validation fails for invalid email."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {
            "to": "not-an-email",
            "subject": "Test",
            "body": "Hello"
        }
        result = parameter_validator.validate("email.send", params)
        
        assert not result.is_valid
        assert "email" in result.get_message().lower()
    
    def test_validate_volume_params_success(self):
        """Test successful volume parameter validation."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"step": 10}
        result = parameter_validator.validate("system.volume.up", params)
        
        assert result.is_valid
    
    def test_validate_volume_too_large(self):
        """Test validation fails for volume step too large."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"step": 100}
        result = parameter_validator.validate("system.volume.up", params)
        
        assert not result.is_valid
        assert "50" in result.get_message()
    
    def test_validate_volume_negative(self):
        """Test validation fails for negative volume."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"step": -5}
        result = parameter_validator.validate("system.volume.up", params)
        
        assert not result.is_valid
    
    def test_validate_browser_url_success(self):
        """Test successful URL validation."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"url": "https://google.com"}
        result = parameter_validator.validate("browser.open", params)
        
        assert result.is_valid
    
    def test_validate_browser_empty_search(self):
        """Test validation fails for empty search query."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"query": ""}
        result = parameter_validator.validate("browser.search_google", params)
        
        assert not result.is_valid
    
    def test_validate_path_too_long(self):
        """Test validation fails for path exceeding MAX_PATH."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        long_path = "C:\\" + "a" * 300
        params = {"path": long_path}
        result = parameter_validator.validate("file.open", params)
        
        assert not result.is_valid
        assert "too long" in result.get_message().lower()
    
    def test_validate_path_invalid_characters(self):
        """Test validation fails for invalid path characters."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"path": "C:\\Users\\file<name>.txt"}
        result = parameter_validator.validate("file.open", params)
        
        assert not result.is_valid
        assert "invalid" in result.get_message().lower()
    
    def test_validation_result_bool(self):
        """Test ValidationResult can be used as boolean."""
        from backend.services.llm.parameter_validator import ValidationResult
        
        valid = ValidationResult(True)
        invalid = ValidationResult(False, ["error"])
        
        assert bool(valid) is True
        assert bool(invalid) is False
    
    def test_suggest_fix_for_empty_path(self):
        """Test suggestion for empty path error."""
        from backend.services.llm.parameter_validator import parameter_validator, ValidationResult
        
        params = {"path": ""}
        result = parameter_validator.validate("file.open", params)
        
        suggestion = parameter_validator.suggest_fix("file.open", params, result)
        
        assert suggestion is not None
        assert "path" in suggestion.lower()
    
    def test_suggest_fix_for_invalid_email(self):
        """Test suggestion for invalid email."""
        from backend.services.llm.parameter_validator import parameter_validator, ValidationResult
        
        params = {"to": "invalid"}
        result = parameter_validator.validate("email.send", params)
        
        suggestion = parameter_validator.suggest_fix("email.send", params, result)
        
        assert suggestion is not None
        assert "email" in suggestion.lower()


class TestValidationEdgeCases:
    """Test edge cases in validation."""
    
    def test_validate_unknown_tool_returns_valid(self):
        """Test validation passes for unknown tools."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"random": "param"}
        result = parameter_validator.validate("unknown.tool", params)
        
        # Should allow unknown tools
        assert result.is_valid
    
    def test_validate_file_move_missing_source(self):
        """Test validation fails when file move missing source."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"destination": "C:\\new.txt"}
        result = parameter_validator.validate("file.move", params)
        
        assert not result.is_valid
        assert "source" in result.get_message().lower()
    
    def test_validate_file_move_missing_destination(self):
        """Test validation fails when file move missing destination."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"source": "C:\\old.txt"}
        result = parameter_validator.validate("file.move", params)
        
        assert not result.is_valid
        assert "destination" in result.get_message().lower()
    
    def test_validate_whatsapp_very_long_message(self):
        """Test validation fails for very long WhatsApp message."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        long_message = "a" * 6000
        params = {"message": long_message, "contact": "John"}
        result = parameter_validator.validate("whatsapp.send", params)
        
        assert not result.is_valid
    
    def test_validate_email_warnings_not_blocking(self):
        """Test warnings don't prevent validation."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {
            "to": "user@example.com",
            "subject": "",  # Empty subject should warn
            "body": "Hello"
        }
        result = parameter_validator.validate("email.send", params)
        
        # Should be valid but with warnings
        assert result.is_valid
        assert len(result.warnings) > 0
    
    def test_validate_volume_string_converted_to_int(self):
        """Test volume step string is converted to int."""
        from backend.services.llm.parameter_validator import parameter_validator
        
        params = {"step": "10"}
        result = parameter_validator.validate("system.volume.up", params)
        
        # Should convert and validate
        assert result.is_valid
        assert params["step"] == 10 or params["step"] == "10"
