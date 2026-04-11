"""
Parameter Validation Module

Validates extracted parameters before execution.
Provides detailed validation errors and suggestions.
"""

import os
import re
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path


class ValidationResult:
    """Result of parameter validation."""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def __bool__(self):
        return self.is_valid
    
    def get_message(self) -> str:
        """Get formatted validation message."""
        if self.is_valid and not self.warnings:
            return "All parameters are valid."
        
        messages = []
        if self.errors:
            messages.append("Errors: " + "; ".join(self.errors))
        if self.warnings:
            messages.append("Warnings: " + "; ".join(self.warnings))
        
        return " ".join(messages)


class ParameterValidator:
    """Validates parameters for tool execution."""
    
    # Email regex
    EMAIL_REGEX = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
    
    # URL regex
    URL_REGEX = re.compile(
        r'^(?:http|https)://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(?:/[^\s]*)?$|'
        r'^[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(?:/[^\s]*)?$'
    )
    
    def __init__(self):
        """Initialize validator."""
        self.max_path_length = 260  # Windows MAX_PATH
        self.max_message_length = 5000
        self.max_email_body_length = 10000
    
    def validate(self, tool_name: str, params: Dict[str, Any]) -> ValidationResult:
        """
        Validate parameters for a specific tool.
        
        Args:
            tool_name: Tool name
            params: Parameters to validate
            
        Returns:
            ValidationResult with validation status and messages
        """
        # Route to specific validator
        if tool_name.startswith("file."):
            return self._validate_file_params(tool_name, params)
        elif tool_name.startswith("folder."):
            return self._validate_folder_params(tool_name, params)
        elif tool_name.startswith("whatsapp"):
            return self._validate_whatsapp_params(params)
        elif tool_name.startswith("email"):
            return self._validate_email_params(params)
        elif tool_name.startswith("system.volume"):
            return self._validate_volume_params(params)
        elif tool_name.startswith("browser"):
            return self._validate_browser_params(params)
        elif tool_name.startswith("app."):
            return self._validate_app_params(params)
        else:
            return ValidationResult(True)  # Unknown tool, allow
    
    def _validate_file_params(self, tool_name: str, params: Dict[str, Any]) -> ValidationResult:
        """Validate file operation parameters."""
        errors = []
        warnings = []
        
        # Validate path parameter
        if "path" in params:
            path_errors, path_warnings = self._validate_path(params["path"], must_exist=(tool_name != "file.create"))
            errors.extend(path_errors)
            warnings.extend(path_warnings)
        
        # Validate source/destination for move operations
        if tool_name == "file.move":
            if "source" not in params:
                errors.append("Missing required parameter: source")
            elif "destination" not in params:
                errors.append("Missing required parameter: destination")
            else:
                # Validate both paths
                src_errors, src_warnings = self._validate_path(params["source"], must_exist=True)
                dst_errors, dst_warnings = self._validate_path(params["destination"], must_exist=False)
                errors.extend([f"Source: {e}" for e in src_errors])
                errors.extend([f"Destination: {e}" for e in dst_errors])
                warnings.extend(src_warnings + dst_warnings)
        
        # Validate content length for create operations
        if "content" in params and len(params["content"]) > 100000:
            warnings.append("Content is very large (>100KB)")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def _validate_folder_params(self, tool_name: str, params: Dict[str, Any]) -> ValidationResult:
        """Validate folder operation parameters."""
        errors = []
        warnings = []
        
        if "path" in params:
            path_errors, path_warnings = self._validate_path(
                params["path"], 
                must_exist=(tool_name == "folder.delete" or tool_name == "folder.open")
            )
            errors.extend(path_errors)
            warnings.extend(path_warnings)
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def _validate_whatsapp_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate WhatsApp parameters."""
        errors = []
        warnings = []
        
        # Validate message
        if "message" not in params or not params["message"]:
            errors.append("Message cannot be empty")
        elif len(params["message"]) > self.max_message_length:
            errors.append(f"Message too long (max {self.max_message_length} characters)")
        
        # Validate contact
        if "contact" not in params or not params["contact"]:
            errors.append("Contact name is required")
        elif len(params["contact"]) < 2:
            warnings.append("Contact name is very short")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def _validate_email_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate email parameters."""
        errors = []
        warnings = []
        
        # Validate recipient email
        if "to" not in params:
            errors.append("Recipient email is required")
        elif not self.EMAIL_REGEX.match(params["to"]):
            errors.append(f"Invalid email address: {params['to']}")
        
        # Validate subject
        if "subject" not in params or not params["subject"]:
            warnings.append("Email subject is empty")
        elif len(params["subject"]) > 200:
            warnings.append("Subject is very long")
        
        # Validate body
        if "body" not in params or not params["body"]:
            warnings.append("Email body is empty")
        elif len(params["body"]) > self.max_email_body_length:
            errors.append(f"Email body too long (max {self.max_email_body_length} characters)")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def _validate_volume_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate volume control parameters."""
        errors = []
        warnings = []
        
        if "step" in params:
            step = params["step"]
            if not isinstance(step, int):
                try:
                    step = int(step)
                    params["step"] = step  # Convert
                except (ValueError, TypeError):
                    errors.append("Volume step must be a number")
                    return ValidationResult(False, errors)
            
            if step < 1:
                errors.append("Volume step must be at least 1")
            elif step > 50:
                errors.append("Volume step too large (max 50)")
            elif step > 20:
                warnings.append("Large volume change (>20)")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def _validate_browser_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate browser parameters."""
        errors = []
        warnings = []
        
        # Validate URL
        if "url" in params:
            url = params["url"]
            if not url:
                errors.append("URL cannot be empty")
            elif not self.URL_REGEX.match(url):
                warnings.append(f"URL format may be invalid: {url}")
        
        # Validate search query
        if "query" in params:
            query = params["query"]
            if not query or len(query.strip()) < 2:
                errors.append("Search query is too short")
            elif len(query) > 500:
                warnings.append("Very long search query")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def _validate_app_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate application launch parameters."""
        errors = []
        warnings = []
        
        if "app_name" not in params or not params["app_name"]:
            errors.append("Application name is required")
        elif len(params["app_name"]) < 2:
            errors.append("Application name too short")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def _validate_path(self, path: str, must_exist: bool = True) -> Tuple[List[str], List[str]]:
        """
        Validate a file/folder path.
        
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check if path is provided
        if not path:
            errors.append("Path cannot be empty")
            return errors, warnings
        
        # Check path length
        if len(path) > self.max_path_length:
            errors.append(f"Path too long (max {self.max_path_length} characters)")
        
        # Check for invalid characters (Windows)
        invalid_chars = '<>"|?*'
        if any(char in path for char in invalid_chars):
            errors.append(f"Path contains invalid characters: {invalid_chars}")
        
        # Check if path exists (if required)
        if must_exist:
            if not os.path.exists(path):
                # Don't add error yet - might be created or different format
                warnings.append(f"Path does not exist: {path}")
        
        # Check if path is absolute
        if not os.path.isabs(path) and ':\\' not in path:
            warnings.append("Relative path detected - may need absolute path")
        
        return errors, warnings
    
    def suggest_fix(self, tool_name: str, params: Dict[str, Any], validation_result: ValidationResult) -> Optional[str]:
        """
        Suggest how to fix validation errors.
        
        Args:
            tool_name: Tool name
            params: Parameters that failed validation
            validation_result: Validation result
            
        Returns:
            Suggestion string or None
        """
        if validation_result.is_valid:
            return None
        
        suggestions = []
        
        # Analyze errors and provide suggestions
        for error in validation_result.errors:
            if "path" in error.lower() and "empty" in error.lower():
                suggestions.append(f"Please provide a file path, e.g., 'C:\\Users\\YourName\\file.txt'")
            elif "email" in error.lower() and "invalid" in error.lower():
                suggestions.append("Please provide a valid email address, e.g., 'user@example.com'")
            elif "message" in error.lower() and "empty" in error.lower():
                suggestions.append("Please provide a message to send")
            elif "contact" in error.lower():
                suggestions.append("Please specify who to send the message to")
            elif "volume" in error.lower():
                suggestions.append("Volume step should be between 1 and 50")
            elif "url" in error.lower():
                suggestions.append("Please provide a valid URL, e.g., 'google.com' or 'https://example.com'")
        
        return " ".join(suggestions) if suggestions else "Please provide all required parameters"


# Global instance
parameter_validator = ParameterValidator()
