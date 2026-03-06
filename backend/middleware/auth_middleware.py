"""Authorization middleware and decorators."""

from functools import wraps
from flask import request, jsonify
from typing import Callable, Optional
from backend.auth.auth_service import AuthService
from backend.database import SessionLocal


def get_token_from_request() -> Optional[str]:
    """Extract JWT token from request headers."""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    # Expected format: "Bearer <token>"
    parts = auth_header.split()
    
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def login_required(f: Callable) -> Callable:
    """
    Decorator to require authentication for a route.
    Adds 'current_user' to request context.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required. Please login.'
            }), 401
        
        # Verify token
        db = SessionLocal()
        try:
            auth_service = AuthService(db)
            valid, message, payload = auth_service.verify_token(token)
            
            if not valid:
                return jsonify({
                    'status': 'error',
                    'message': message
                }), 401
            
            # Get user from database
            user = auth_service.get_user_by_id(payload['user_id'])
            
            if not user or not user.is_active:
                return jsonify({
                    'status': 'error',
                    'message': 'User not found or inactive'
                }), 401
            
            # Add user to request context
            request.current_user = user
            
            return f(*args, **kwargs)
            
        finally:
            db.close()
    
    return decorated_function


def admin_required(f: Callable) -> Callable:
    """
    Decorator to require admin role for a route.
    Must be used with @login_required.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user exists in request (added by login_required)
        if not hasattr(request, 'current_user'):
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        # Check if user is admin
        if request.current_user.role != 'admin':
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def role_required(required_role: str) -> Callable:
    """
    Decorator factory to require a specific role.
    Usage: @role_required('admin')
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required'
                }), 401
            
            if request.current_user.role != required_role:
                return jsonify({
                    'status': 'error',
                    'message': f'{required_role.capitalize()} access required'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
