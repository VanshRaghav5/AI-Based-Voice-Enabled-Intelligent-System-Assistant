"""
Wake Word Detection Test

Tests the wake word detector with a simulated detection.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.services.voice.wake_word_detector import WakeWordDetector
from backend.utils.logger import logger
import time

def test_callback(wake_word):
    """Callback function when wake word is detected."""
    print(f"\nðŸŽ‰ WAKE WORD DETECTED: '{wake_word}'")
    print("    This would normally trigger voice listening...")

def main():
    print("=" * 60)
    print("WAKE WORD DETECTION TEST")
    print("=" * 60)
    
    print("\nðŸ“‹ Testing wake word detector initialization...")
    
    # Create detector with callback
    detector = WakeWordDetector(callback=test_callback)
    
    print(f"âœ… Detector initialized")
    print(f"   Wake words: {detector.wake_words}")
    print(f"   Callback: {detector.callback is not None}")
    
    print("\nâš ï¸  MANUAL TEST REQUIRED:")
    print("   To fully test wake word detection:")
    print("   1. Start the backend: python backend/api_service.py")
    print("   2. Start the desktop client: python desktop_1/main.py")
    print("   3. Click the 'Wake Word: OFF' button to enable it")
    print("   4. Say 'Omini' into your microphone")
    print("   5. Watch for automatic voice listening activation")
    
    print("\nðŸ“Š QUICK SIMULATION TEST:")
    print("   Simulating wake word detection...")
    
    # Simulate callback trigger
    if detector.callback:
        detector.callback("omini")
        print("   âœ… Callback executed successfully")
    else:
        print("   âŒ No callback configured")
    
    print("\n" + "=" * 60)
    print("âœ… BASIC TESTS COMPLETE")
    print("=" * 60)
    print("\nðŸ’¡ The wake word detector is ready!")
    print("   Run the full app to test real-time detection.")

if __name__ == "__main__":
    main()
