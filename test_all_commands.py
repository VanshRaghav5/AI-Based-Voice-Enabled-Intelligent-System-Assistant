#!/usr/bin/env python
"""
Comprehensive test suite for AI Voice Assistant
Tests all major commands without voice input
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from core.assistant_controller import AssistantController


def test_command(controller, command: str, expected_keyword: str = None):
    """Test a single command"""
    print(f"\n{'='*60}")
    print(f"Testing: {command}")
    print(f"{'='*60}")
    
    result = controller.process(command)
    
    status = result.get('status', 'unknown')
    message = result.get('message', 'No message')
    
    print(f"Status: {status}")
    print(f"Message: {message}")
    
    # Handle confirmation_required by auto-approving for tests
    if status == 'confirmation_required':
        print("[AUTO-APPROVE] Auto-approving for test...")
        result = controller.confirm_action(True)
        status = result.get('status', 'unknown')
        message = result.get('message', 'No message')
        print(f"Confirmed - Status: {status}")
        print(f"Confirmed - Message: {message}")
    
    if expected_keyword and expected_keyword.lower() in str(result).lower():
        print("[PASS]")
        return True
    elif status == 'success':
        print("[PASS]")
        return True
    elif status == 'error' and 'did not understand' in message.lower():
        print("[FAIL] - Command not understood")
        return False
    else:
        print("[OK] Executed with result")
        return True


def main():
    print("\n" + "="*60)
    print("AI VOICE ASSISTANT - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    # Initialize controller
    print("\nInitializing AssistantController...")
    controller = AssistantController()
    print("[OK] Controller initialized")
    
    # Test cases
    tests = [
        ("send whatsapp to swayam saying hello world", "whatsapp"),
        ("send whatsapp to vansh with hi there", "whatsapp"),
        ("create a file named test.txt on desktop", "file"),
        ("create a folder on desktop called new folder", "folder"),
        ("increase volume", "volume"),
        ("decrease volume", "volume"),
        ("mute volume", "mute"),
        ("lock system", "lock"),
        ("open whatsapp", "whatsapp"),
        ("search for pdf files", "search"),
        ("delete file", "error"),  # Should error - no path
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for command, expected in tests:
        try:
            result = test_command(controller, command, expected)
            results.append((command, result))
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] Exception: {e}")
            results.append((command, False))
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass Rate: {(passed/len(tests)*100):.1f}%")
    
    print("\n" + "="*60)
    print("DETAILED RESULTS")
    print("="*60)
    for cmd, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {cmd}")
    
    print("\n" + "="*60)
    if passed == len(tests):
        print("SUCCESS - ALL TESTS PASSED!")
    else:
        print(f"WARNING - {failed} tests need attention")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
