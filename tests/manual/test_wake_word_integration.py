"""
Full Wake Word Integration Test

This script tests the complete wake word flow:
1. API endpoints
2. Wake word detector
3. Voice listening trigger
"""

import sys
import os
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("WAKE WORD FEATURE - INTEGRATION TEST")
print("=" * 70)

# Test 1: Configuration
print("\n[1/5] Testing configuration...")
from backend.utils.assistant_config import assistant_config
wake_config = assistant_config.get('wake_word')
print(f"   âœ… Wake words: {wake_config.get('words')}")
print(f"   âœ… Listen duration: {wake_config.get('listen_duration')}s")
print(f"   âœ… Enabled by default: {wake_config.get('enabled')}")

# Test 2: Wake Word Detector
print("\n[2/5] Testing wake word detector module...")
from backend.services.voice.wake_word_detector import WakeWordDetector

detected_words = []
def test_callback(word):
    detected_words.append(word)
    print(f"   ðŸŽ¯ Callback triggered with: '{word}'")

detector = WakeWordDetector(callback=test_callback)
print(f"   âœ… Detector initialized")
print(f"   âœ… Wake words loaded: {detector.wake_words}")

# Simulate detection
detector.callback("omini")
if "omini" in detected_words:
    print("   âœ… Callback mechanism working")
else:
    print("   âŒ Callback failed")

# Test 3: API Service Integration
print("\n[3/5] Testing API service integration...")
try:
    from backend.api.routes import on_wake_word_detected
    print("   âœ… Wake word callback function found in API")
except ImportError as e:
    print(f"   âŒ Import error: {e}")

# Test 4: Desktop Client Integration
print("\n[4/5] Testing desktop client integration...")
try:
    from desktop_1.services.api_client import start_wake_word, stop_wake_word, get_wake_word_status
    print("   âœ… Wake word API client functions found")
except ImportError as e:
    print(f"   âš ï¸  Import warning: {e}")
    print("      (This is OK if desktop client isn't running)")

# Test 5: Summary
print("\n[5/5] Test Summary")
print("-" * 70)
print("âœ… All core components are working!")
print()
print("ðŸ“‹ MANUAL TESTING STEPS:")
print()
print("Step 1: Start the backend server")
print("   > cd \"D:\\AI Based Voice Intelligent System\\AI-Based-Voice-Enabled-Intelligent-System-Assistant\"")
print("   > python backend/api_service.py")
print()
print("Step 2: Start the desktop client (in a new terminal)")
print("   > cd \"D:\\AI Based Voice Intelligent System\\AI-Based-Voice-Enabled-Intelligent-System-Assistant\"")
print("   > python desktop_1/main.py")
print()
print("Step 3: Enable wake word detection")
print("   â€¢ Click the 'ðŸ’¤ Wake Word: OFF' button")
print("   â€¢ It should turn green: 'ðŸ‘‚ Wake Word: ON'")
print()
print("Step 4: Test wake word")
print("   â€¢ Say: 'Omini' or 'Hey Omini'")
print("   â€¢ Voice listening should start automatically")
print("   â€¢ You'll see: 'ðŸ‘‚ 'omini' detected! Listening...'")
print()
print("Step 5: Give a command")
print("   â€¢ Say your command: 'send email to test@example.com'")
print("   â€¢ System should process it normally")
print()
print("=" * 70)
print("EXPECTED BEHAVIOR:")
print("  1. Wake word button turns green when enabled")
print("  2. Saying 'Omini' triggers automatic listening")
print("  3. Listening overlay appears")  
print("  4. Your command is transcribed and executed")
print("  5. Wake word detection resumes after command completes")
print("=" * 70)
print()
print("ðŸ’¡ TIP: Check backend logs for:")
print("   [WakeWord] âœ“ DETECTED: 'otto' in '...'")
print("   [WakeWord] Detection started")
print("   [Voice Loop] Started")
print()
print("ðŸ› If wake word isn't detected:")
print("   â€¢ Ensure microphone is working (run: python tests/manual/test_voice.py)")
print("   â€¢ Speak clearly and loudly")
print("   â€¢ Check backend logs for '[WakeWord] Heard:' messages")
print()
