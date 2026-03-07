"""Input validation schemas using Marshmallow."""

from marshmallow import Schema, fields, validate, validates, ValidationError
import re


class LoginSchema(Schema):
    """Schema for login validation."""
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50),
        error_messages={'required': 'Username is required'}
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=100),
        error_messages={'required': 'Password is required'}
    )


class RegisterSchema(Schema):
    """Schema for user registration validation."""
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50),
        error_messages={'required': 'Username is required'}
    )
    email = fields.Email(
        required=True,
        error_messages={'required': 'Email is required'}
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=100),
        error_messages={'required': 'Password is required'}
    )
    
    @validates('username')
    def validate_username(self, value, **kwargs):
        """Validate username format."""
        # Only allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValidationError('Username can only contain letters, numbers, and underscores')
    
    @validates('password')
    def validate_password(self, value, **kwargs):
        """Validate password strength."""
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', value):
            raise ValidationError('Password must contain at least one number')


class CommandSchema(Schema):
    """Schema for command input validation."""
    command = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=1000),
        error_messages={'required': 'Command is required'}
    )
    
    @validates('command')
    def validate_command(self, value, **kwargs):
        """Sanitize command input."""
        # Remove any potentially dangerous characters
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'onclick=',
            r'eval\(',
            r'exec\('
        ]
        
        value_lower = value.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, value_lower):
                raise ValidationError('Command contains potentially dangerous content')


class SettingsSchema(Schema):
    """Schema for settings validation."""
    persona = fields.Str(
        validate=validate.OneOf(['butler', 'professional', 'friendly', 'concise']),
        allow_none=True
    )
    language = fields.Str(
        validate=validate.OneOf(['english', 'hindi', 'spanish', 'french', 'german']),
        allow_none=True
    )
    memory_enabled = fields.Bool(allow_none=True)


def sanitize_input(data: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        data: Input string to sanitize
        
    Returns:
        Sanitized string
    """
    if not isinstance(data, str):
        return data
    
    # Remove null bytes
    data = data.replace('\x00', '')
    
    # Trim whitespace
    data = data.strip()
    
    # Escape special characters for SQL (though SQLAlchemy handles this)
    # This is an additional layer of defense
    data = data.replace("'", "''").replace('"', '""')
    
    return data
