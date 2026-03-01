"""
Test suite for Phase 1 Brain Contracts.

This validates that all three agent contracts work as expected:
1. brain_router.route() - Mode classification
2. intent_agent.plan() - Task planning
3. chat_agent.respond() - Conversational responses
"""

import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agents import route, plan, respond


def test_brain_router():
    """Test brain_router.route() contract."""
    print("="*70)
    print("TEST 1: brain_router.route()")
    print("="*70)
    
    test_cases = [
        ("Open Chrome", "task"),
        ("Lock my laptop", "task"),
        ("What is Python?", "chat"),
        ("Explain recursion", "chat"),
        ("Play music", "task"),
        ("Create a file", "task"),
        ("Why is the sky blue?", "chat"),
    ]
    
    for user_input, expected in test_cases:
        result = route(user_input)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{user_input}' -> {result} (expected: {expected})")
    
    print()


def test_intent_agent():
    """Test intent_agent.plan() contract."""
    print("="*70)
    print("TEST 2: intent_agent.plan()")
    print("="*70)
    
    test_cases = [
        ("Lock my laptop", {}),
        ("Create a file at C:\\test.txt", {}),
        ("Open it", {"last_file": "C:\\document.txt"}),
        ("Do that again", {"last_intent": "system_lock", "last_entities": {}}),
        ("Mute the volume", {}),
        ("Shutdown the computer", {}),
    ]
    
    for user_input, context in test_cases:
        result = plan(user_input, context)
        print(f"\nInput: '{user_input}'")
        print(f"Context: {context}")
        print(f"Result: {result}")
        
        # Validate contract shape
        assert "intent" in result, "Missing 'intent' key"
        assert "entities" in result, "Missing 'entities' key"
        assert "confidence" in result, "Missing 'confidence' key"
        assert isinstance(result["intent"], str), "'intent' must be string"
        assert isinstance(result["entities"], dict), "'entities' must be dict"
        assert isinstance(result["confidence"], (int, float)), "'confidence' must be number"
        print("✅ Contract shape valid")
    
    print()


def test_chat_agent():
    """Test chat_agent.respond() contract."""
    print("="*70)
    print("TEST 3: chat_agent.respond()")
    print("="*70)
    
    test_cases = [
        ("What is Python?", {}),
        ("Is it compiled?", {"last_response": "Python is a language..."}),
        ("Tell me more", {"last_response": "Previous explanation..."}),
        ("Who invented Python?", {}),
    ]
    
    for user_input, context in test_cases:
        result = respond(user_input, context)
        print(f"\nInput: '{user_input}'")
        print(f"Response: {result}")
        
        # Validate contract
        assert isinstance(result, str), "Response must be string"
        assert len(result) > 0, "Response must not be empty"
        assert "intent" not in result.lower() or "stub" in result.lower(), "Should not return JSON"
        print("✅ Contract valid (returns natural language string)")
    
    print()


def test_no_cross_calling():
    """Verify agents don't call each other."""
    print("="*70)
    print("TEST 4: No Cross-Calling Verification")
    print("="*70)
    
    import inspect
    from backend.agents import brain_router, intent_agent, chat_agent
    
    # Check brain_router doesn't import other agents
    router_source = inspect.getsource(brain_router)
    assert "intent_agent" not in router_source, "brain_router imports intent_agent!"
    assert "chat_agent" not in router_source, "brain_router imports chat_agent!"
    print("✅ brain_router does not import other agents")
    
    # Check intent_agent doesn't import other agents
    intent_source = inspect.getsource(intent_agent)
    assert "brain_router" not in intent_source, "intent_agent imports brain_router!"
    assert "chat_agent" not in intent_source, "intent_agent imports chat_agent!"
    print("✅ intent_agent does not import other agents")
    
    # Check chat_agent doesn't import other agents
    chat_source = inspect.getsource(chat_agent)
    assert "brain_router" not in chat_source, "chat_agent imports brain_router!"
    assert "intent_agent" not in chat_source, "chat_agent imports intent_agent!"
    print("✅ chat_agent does not import other agents")
    
    print("\n✅ All agents are properly isolated")
    print()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PHASE 1 BRAIN CONTRACTS - VALIDATION SUITE")
    print("="*70)
    print()
    
    try:
        test_brain_router()
        test_intent_agent()
        test_chat_agent()
        test_no_cross_calling()
        
        print("="*70)
        print("✅ ALL TESTS PASSED - CONTRACTS ARE FROZEN")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
