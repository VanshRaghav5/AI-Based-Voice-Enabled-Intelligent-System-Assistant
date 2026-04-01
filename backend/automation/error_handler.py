# backend/automation/error_handler.py

from typing import Dict, Optional, Callable
from backend.config.logger import logger


class AutomationError(Exception):
    """Base exception for automation errors"""
    
    def __init__(self, message: str, user_message: str = None, details: Dict = None):
        super().__init__(message)
        self.message = message
        self.user_message = user_message or message
        self.details = details or {}


class WindowNotFoundError(AutomationError):
    """Raised when required window is not found"""
    pass


class ProcessNotRunningError(AutomationError):
    """Raised when required process is not running"""
    pass


class AutomationTimeoutError(AutomationError):
    """Raised when automation operation times out"""
    pass


class ErrorHandler:
    """Centralized error handling with user-friendly messages and fallback support"""
    
    # Default user-friendly error messages for TTS
    ERROR_MESSAGES = {
        "window_not_found": "I couldn't find the {app} window. Please make sure it's open and try again.",
        "process_not_running": "The {app} application is not running. Would you like me to open it first?",
        "timeout": "The operation took too long to complete. Please try again.",
        "permission_denied": "I don't have permission to perform that action.",
        "file_not_found": "The file or folder was not found at the specified location.",
        "file_exists": "The target file or folder already exists.",
        "network_error": "There was a network connection problem. Please check your internet connection.",
        "config_missing": "The required configuration is missing. Please set up {config} first.",
        "automation_failed": "The automation task failed. {reason}",
        "unknown_error": "Something went wrong. Please try again or contact support.",
    }
    
    # Fallback actions for common errors
    FALLBACK_ACTIONS = {
        "process_not_running": "open_app",
        "window_not_found": "retry_with_delay",
        "timeout": "retry_once",
    }
    
    @staticmethod
    def handle_error(
        error: Exception,
        operation: str,
        fallback: Optional[Callable] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Handle an error with logging, user message, and optional fallback
        
        Args:
            error: The exception that occurred
            operation: Name of the operation that failed
            fallback: Optional fallback function to execute
            context: Additional context information
            
        Returns:
            Structured error response
        """
        context = context or {}
        
        # Log the technical error
        logger.error(f"[{operation}] Error: {str(error)}", exc_info=True)
        
        # Determine user message
        if isinstance(error, AutomationError):
            user_message = error.user_message
            details = error.details
        else:
            user_message = ErrorHandler._get_user_friendly_message(error, operation, context)
            details = {"error_type": type(error).__name__}
        
        # Try fallback if provided
        fallback_result = None
        if fallback:
            try:
                logger.info(f"[{operation}] Attempting fallback action")
                fallback_result = fallback()
                logger.info(f"[{operation}] Fallback succeeded")
            except Exception as fallback_error:
                logger.error(f"[{operation}] Fallback failed: {fallback_error}")
        
        return {
            "status": "error",
            "message": user_message,
            "data": {
                "operation": operation,
                "error_type": type(error).__name__,
                "technical_error": str(error),
                "fallback_attempted": fallback is not None,
                "fallback_succeeded": fallback_result is not None,
                **details,
                **context
            }
        }
    
    @staticmethod
    def _get_user_friendly_message(error: Exception, operation: str, context: Dict) -> str:
        """Generate user-friendly error message based on error type"""
        
        error_str = str(error).lower()

        if isinstance(error, FileExistsError) or "already exists" in error_str or "exists" in error_str:
            return ErrorHandler.ERROR_MESSAGES["file_exists"]
        
        # Match common error patterns
        if "file" in error_str or "path" in error_str:
            return ErrorHandler.ERROR_MESSAGES["file_not_found"]

        if "window" in error_str or "not found" in error_str:
            app = context.get("app", "required application")
            return ErrorHandler.ERROR_MESSAGES["window_not_found"].format(app=app)
        
        elif "process" in error_str or "not running" in error_str:
            app = context.get("app", "application")
            return ErrorHandler.ERROR_MESSAGES["process_not_running"].format(app=app)
        
        elif "timeout" in error_str or "timed out" in error_str:
            return ErrorHandler.ERROR_MESSAGES["timeout"]
        
        elif "permission" in error_str or "access denied" in error_str:
            return ErrorHandler.ERROR_MESSAGES["permission_denied"]
        
        elif "network" in error_str or "connection" in error_str:
            return ErrorHandler.ERROR_MESSAGES["network_error"]
        
        elif "config" in error_str or "missing" in error_str:
            config = context.get("config", "the configuration")
            return ErrorHandler.ERROR_MESSAGES["config_missing"].format(config=config)
        
        else:
            reason = str(error) if len(str(error)) < 100 else "Unknown reason"
            return ErrorHandler.ERROR_MESSAGES["automation_failed"].format(reason=reason)
    
    @staticmethod
    def wrap_automation(
        func: Callable,
        operation_name: str,
        context: Optional[Dict] = None,
        fallback: Optional[Callable] = None
    ) -> Dict:
        """
        Wrap an automation function with comprehensive error handling
        
        Args:
            func: The automation function to execute
            operation_name: Name for logging/error messages
            context: Additional context
            fallback: Optional fallback function
            
        Returns:
            Structured response (success or error)
        """
        try:
            result = func()
            
            # If function returns dict with status, use it
            if isinstance(result, dict) and "status" in result:
                if result["status"] == "success":
                    logger.info(f"[{operation_name}] Operation succeeded")
                return result
            
            # Otherwise, treat as success
            logger.info(f"[{operation_name}] Operation succeeded")
            return {
                "status": "success",
                "message": f"{operation_name} completed successfully",
                "data": result if isinstance(result, dict) else {}
            }
            
        except Exception as e:
            return ErrorHandler.handle_error(e, operation_name, fallback, context)


# Convenience instance
error_handler = ErrorHandler()
