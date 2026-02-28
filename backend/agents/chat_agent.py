"""Chat agent for conversational responses."""
from __future__ import annotations


def respond(user_input: str, context: dict) -> str:
    """
    Generate a conversational response to user input.
    
    This function handles all non-task interactions. It produces natural
    language responses for questions, explanations, definitions, and
    general conversation.
    
    Design principles:
    - Returns ONLY natural language strings (never JSON)
    - NO tool calls
    - NO execution
    - NO planning
    - Uses context for conversation continuity
    
    This agent exists to make the system feel conversational and intelligent
    when users aren't giving commands. It should never attempt to execute
    actions or return structured data.
    
    Args:
        user_input: Raw user text input
        context: Dictionary containing conversation history and state
            Expected keys:
                - "last_response" (str): Previous assistant message
                - "conversation_history" (list): Recent message pairs
                - "user_name" (str, optional): User's name
                - "session_start" (str, optional): Session timestamp
    
    Returns:
        Natural language string response
        
    Examples:
        >>> respond("What is Python?", {})
        "Python is a high-level, interpreted programming language..."
        
        >>> respond("Is it compiled?", {"last_response": "Python is..."})
        "Python is primarily interpreted, but it does use..."
        
        >>> respond("Tell me more", {"last_response": "..."})
        "Continuing from before, Python was created by..."
    
    Notes:
        - This is currently a STUB implementation
        - Will be connected to LLM in Phase 2
        - For now, returns placeholder responses
    """
    # STUB IMPLEMENTATION — Phase 1 contract only
    # This will be replaced with actual LLM integration in Phase 2
    
    user_lower = user_input.lower().strip()
    
    # Handle common patterns with placeholder responses
    if "what is" in user_lower or "what's" in user_lower:
        topic = user_input.split("is")[-1].strip(" ?")
        return f"I'd explain {topic} here, but I'm still learning. (LLM integration pending)"
    
    if "how do" in user_lower or "how to" in user_lower:
        return "I'd provide step-by-step instructions here. (LLM integration pending)"
    
    if "why" in user_lower:
        return "I'd explain the reasoning here. (LLM integration pending)"
    
    if "who" in user_lower:
        return "I'd provide information about that person or entity. (LLM integration pending)"
    
    if "when" in user_lower:
        return "I'd provide timing or historical information. (LLM integration pending)"
    
    if "where" in user_lower:
        return "I'd provide location information. (LLM integration pending)"
    
    # Check if this is a follow-up question
    if context.get("last_response"):
        if any(word in user_lower for word in ["more", "continue", "elaborate", "example"]):
            return "I'd expand on my previous response here. (LLM integration pending)"
    
    # Generic fallback
    return (
        "I understand you're asking about something, but I'm currently "
        "in stub mode. Full conversational AI coming in Phase 2!"
    )
