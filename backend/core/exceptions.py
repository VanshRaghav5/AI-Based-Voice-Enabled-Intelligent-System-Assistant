"""
Custom exceptions for the agent system.
"""


class AgentException(Exception):
    """Base exception for agent-related errors."""
    pass


class PlannerException(AgentException):
    """Exception raised by the planner."""
    pass


class ExecutorException(AgentException):
    """Exception raised by the executor."""
    pass


class ToolException(AgentException):
    """Exception raised by tool execution."""
    pass


class ToolNotFound(ToolException):
    """Exception raised when a tool is not found in registry."""
    pass


class InvalidToolCall(ToolException):
    """Exception raised when a tool call is invalid."""
    pass
