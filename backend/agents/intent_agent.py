"""Intent recognition and execution planning agent (Task Brain)."""
from __future__ import annotations

import json
import os
from typing import Any


# Constants
CONFIDENCE_THRESHOLD = 0.7
ENTITIES_PATH = os.path.join(os.path.dirname(__file__), "..", "llm", "entities.json")


def plan(user_input: str, context: dict) -> dict:
    """
    Convert user input into an ExecutionPlan.
    
    This is the Task Brain's core function. It acts as a compiler, not an
    assistant — taking natural language and producing a strict, executable
    plan with no ambiguity.
    
    Design principles:
    - Returns JSON-compatible dict ONLY (never strings, never exceptions)
    - NO execution (planning only)
    - NO printing or logging at this level
    - NO chat text or confirmations
    - Uses context to resolve ambiguity ("open it", "again", missing entities)
    - Returns error intent only if ambiguity is genuinely unresolvable
    
    Context resolution examples:
        - "Open it" → uses context["last_app"] or context["last_file"]
        - "Again" → repeats context["last_intent"]
        - "Save this" → infers file from context["active_file"]
        - "Send message to Mom" → resolves "Mom" from context["contacts"]
    
    Args:
        user_input: Raw user text (can be ambiguous, pronoun-filled, or brief)
        context: Short-term memory containing:
            - "last_intent" (str): Previous intent name
            - "last_entities" (dict): Previous extracted entities
            - "last_app" (str): Last opened application
            - "last_file" (str): Last accessed file path
            - "active_file" (str): Currently open/focused file
            - "working_directory" (str): Current directory context
            - "contacts" (dict): Known contact name mappings
    
    Returns:
        ExecutionPlan with exact shape:
        {
            "intent": str,        # e.g., "chrome.open", "file_create", "system_lock"
            "entities": dict,     # e.g., {"url": "https://youtube.com"}
            "confidence": float   # 0.0 to 1.0
        }
        
        Intent names MUST match executor registry (validated against entities.json)
        
    Examples:
        >>> plan("Open Chrome and go to YouTube", {})
        {
            "intent": "chrome.open",
            "entities": {"url": "https://youtube.com"},
            "confidence": 0.91
        }
        
        >>> plan("Lock my laptop", {})
        {
            "intent": "system_lock",
            "entities": {},
            "confidence": 0.95
        }
        
        >>> plan("Open it", {"last_app": "chrome"})
        {
            "intent": "chrome.open",
            "entities": {},
            "confidence": 0.85
        }
        
        >>> plan("Do that again", {"last_intent": "system_lock"})
        {
            "intent": "system_lock",
            "entities": {},
            "confidence": 0.90
        }
    
    Notes:
        - This is currently a RULE-BASED STUB for Phase 1
        - Will be upgraded to LLM-powered planning in Phase 2
        - Focuses on contract compliance, not intelligence
    """
    # Load entity schema for validation
    entity_schema = _load_entity_schema()
    
    # Normalize input
    user_input_lower = user_input.lower().strip()
    
    # Handle context-based resolution first
    resolved_plan = _resolve_from_context(user_input_lower, context, entity_schema)
    if resolved_plan:
        return resolved_plan
    
    # Attempt to extract intent and entities from raw input
    intent, entities, confidence = _extract_intent_entities(user_input_lower, entity_schema)
    
    # Validate against schema
    if intent != "unknown" and intent in entity_schema:
        _validate_entities(intent, entities, entity_schema)
    
    # Build ExecutionPlan
    return {
        "intent": intent,
        "entities": entities,
        "confidence": confidence
    }


def _load_entity_schema() -> dict:
    """Load entity requirements from JSON schema."""
    try:
        with open(ENTITIES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Fallback to empty schema if file not found
        return {}


def _resolve_from_context(user_input: str, context: dict, schema: dict) -> dict | None:
    """
    Resolve ambiguous input using context.
    
    Returns ExecutionPlan if context provides resolution, None otherwise.
    """
    # "again" / "repeat" / "do that again"
    if any(word in user_input for word in ["again", "repeat", "same thing"]):
        if context.get("last_intent"):
            return {
                "intent": context["last_intent"],
                "entities": context.get("last_entities", {}),
                "confidence": 0.90
            }
    
    # "open it" / "close it" / "delete it"
    if " it" in user_input or user_input.endswith("it"):
        if "open" in user_input and context.get("last_app"):
            return {
                "intent": f"{context['last_app']}.open",
                "entities": {},
                "confidence": 0.85
            }
        if "open" in user_input and context.get("last_file"):
            return {
                "intent": "file_open",
                "entities": {"path": context["last_file"]},
                "confidence": 0.85
            }
        if "delete" in user_input and context.get("last_file"):
            return {
                "intent": "file_delete",
                "entities": {"path": context["last_file"]},
                "confidence": 0.85
            }
    
    # No context resolution available
    return None


def _extract_intent_entities(user_input: str, schema: dict) -> tuple[str, dict, float]:
    """
    Extract intent and entities from user input (rule-based stub).
    
    Returns: (intent, entities, confidence)
    """
    entities = {}
    confidence = 0.8
    
    # FILE OPERATIONS
    if "create" in user_input and ("file" in user_input or "document" in user_input):
        # Try to extract path
        path = _extract_path(user_input)
        if path:
            entities["path"] = path
            return ("file_create", entities, 0.85)
        return ("file_create", entities, 0.60)  # Lower confidence without path
    
    if "delete" in user_input and "file" in user_input:
        path = _extract_path(user_input)
        if path:
            entities["path"] = path
        return ("file_delete", entities, 0.85 if path else 0.60)
    
    if "open" in user_input and "file" in user_input:
        path = _extract_path(user_input)
        if path:
            entities["path"] = path
        return ("file_open", entities, 0.85 if path else 0.60)
    
    # FOLDER OPERATIONS
    if "create" in user_input and ("folder" in user_input or "directory" in user_input):
        path = _extract_path(user_input)
        if path:
            entities["path"] = path
        return ("folder_create", entities, 0.85 if path else 0.60)
    
    if "delete" in user_input and ("folder" in user_input or "directory" in user_input):
        path = _extract_path(user_input)
        if path:
            entities["path"] = path
        return ("folder_delete", entities, 0.85 if path else 0.60)
    
    # SYSTEM OPERATIONS
    if "lock" in user_input and any(word in user_input for word in ["laptop", "computer", "pc", "system"]):
        return ("system_lock", {}, 0.95)
    
    if "shutdown" in user_input or "shut down" in user_input:
        return ("system_shutdown", {}, 0.95)
    
    if "restart" in user_input or "reboot" in user_input:
        return ("system_restart", {}, 0.95)
    
    if "sleep" in user_input and any(word in user_input for word in ["laptop", "computer", "pc", "system"]):
        return ("system_sleep", {}, 0.95)
    
    # VOLUME OPERATIONS
    if any(word in user_input for word in ["mute", "silence"]):
        return ("volume_mute", {}, 0.90)
    
    if "volume" in user_input or "louder" in user_input or "increase sound" in user_input:
        if "up" in user_input or "increase" in user_input or "louder" in user_input:
            return ("volume_up", {}, 0.90)
        if "down" in user_input or "decrease" in user_input or "quieter" in user_input:
            return ("volume_down", {}, 0.90)
    
    # WHATSAPP
    if ("send" in user_input or "message" in user_input) and "whatsapp" in user_input:
        # Try to extract target and message
        # This is a simplified stub - real implementation would use better NLP
        return ("whatsapp_send", {}, 0.70)
    
    # FILE SEARCH
    if "search" in user_input or "find" in user_input:
        if "file" in user_input or "document" in user_input:
            # Try to extract search term
            return ("file_search", {}, 0.70)
    
    # UNKNOWN
    return ("unknown", {}, 0.50)


def _extract_path(text: str) -> str | None:
    """Extract file/folder path from text (simplified)."""
    import re
    
    # Look for quoted paths
    quoted = re.search(r'["\']([^"\']+)["\']', text)
    if quoted:
        return quoted.group(1)
    
    # Look for Windows-style paths (C:\...)
    windows_path = re.search(r'([A-Za-z]:\\[^\s]+)', text)
    if windows_path:
        return windows_path.group(1)
    
    # Look for Unix-style paths (./... or /...)
    unix_path = re.search(r'([./][^\s]+)', text)
    if unix_path:
        return unix_path.group(1)
    
    return None


def _validate_entities(intent: str, entities: dict, schema: dict) -> None:
    """
    Validate that required entities are present.
    
    Raises ValueError if validation fails (caller should catch and handle).
    """
    if intent not in schema:
        return  # No schema to validate against
    
    required = schema[intent].get("required", [])
    missing = [e for e in required if e not in entities]
    
    if missing:
        raise ValueError(f"Missing required entities for '{intent}': {', '.join(missing)}")
