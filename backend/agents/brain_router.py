"""Brain router for mode classification (task vs chat)."""
from __future__ import annotations


def route(user_input: str) -> str:
    """
    Decide whether user input is a task or chat request.
    
    This function uses deterministic, keyword-based routing to classify
    user intent into one of two modes:
    - "task": User wants the system to DO something (execute an action)
    - "chat": User wants to ASK something (conversational response)
    
    Design principles:
    - NO LLM calls (deterministic only)
    - NO memory access
    - NO entity extraction
    - NO side effects
    - Misclassification is acceptable; ambiguity is acceptable
    
    The controller is responsible for handling edge cases. This function
    prioritizes predictability over accuracy.
    
    Args:
        user_input: Raw user text input (pre-cleaned, lowercase recommended)
    
    Returns:
        Either "task" or "chat"
        
    Examples:
        >>> route("open chrome")
        "task"
        >>> route("what is python")
        "chat"
        >>> route("lock my laptop")
        "task"
        >>> route("explain recursion")
        "chat"
        >>> route("play music")
        "task"
    """
    input_lower = user_input.lower().strip()
    
    # Task action verbs (things to DO)
    task_keywords = [
        # Application control
        "open", "close", "launch", "start", "stop", "kill", "run",
        # File operations
        "create", "delete", "move", "copy", "rename", "save", "write",
        # System control
        "lock", "unlock", "shutdown", "restart", "sleep", "hibernate",
        # Media control
        "play", "pause", "resume", "skip", "next", "previous", "mute", "unmute",
        # Volume control
        "volume", "louder", "quieter", "increase", "decrease",
        # Communication
        "send", "message", "call", "email", "text",
        # Search actions
        "find", "search", "locate",
        # Navigation
        "go to", "navigate", "visit",
    ]
    
    # Chat question indicators (things to ASK)
    chat_keywords = [
        # Question words
        "what", "why", "how", "when", "where", "who", "which",
        # Explanation requests
        "explain", "tell me", "describe", "define", "meaning",
        # Information requests
        "is it", "are you", "can you", "do you know", "help me understand",
        # Learning
        "teach", "learn", "show me how", "difference between",
    ]
    
    # Check for task indicators first (tasks are more specific)
    for keyword in task_keywords:
        if keyword in input_lower:
            return "task"
    
    # Check for chat indicators
    for keyword in chat_keywords:
        if input_lower.startswith(keyword) or f" {keyword} " in f" {input_lower} ":
            return "chat"
    
    # Default heuristic: questions are chat, imperatives are tasks
    if "?" in user_input:
        return "chat"
    
    # If starts with a verb-like pattern, probably a task
    first_word = input_lower.split()[0] if input_lower.split() else ""
    if len(first_word) > 2 and not first_word in ["the", "a", "an", "my", "your"]:
        return "task"
    
    # Default to chat for safety (less destructive if wrong)
    return "chat"
