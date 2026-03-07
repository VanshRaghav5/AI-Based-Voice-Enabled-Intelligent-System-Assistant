"""
Voice Module Diagnostic Test
Tests microphone access, recording, and STT functionality
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.voice_engine.input.recorder import record_audio_fixed, record_audio_until_silence
from backend.voice_engine.stt.whisper_engine import transcribe_audio
from backend.config.logger import logger
import sounddevice as sd

def list_audio_devices():
    """List all available audio input devices."""
    print("\n=== Available Audio Devices ===")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"[{i}] {device['name']}")
            print(f"    Channels: {device['max_input_channels']}")
            print(f"    Sample Rate: {device['default_samplerate']}")
    print()


def test_microphone():
    """Test if microphone can record audio."""
    print("\n=== Testing Microphone ===")
    try:
        print("Recording 3 seconds of audio...")
        audio_path = record_audio_fixed(duration=3.0)
        
        if not audio_path:
            print("❌ Failed to record audio")
            return False
        
        print(f"✅ Audio recorded successfully: {audio_path}")
        file_size = os.path.getsize(audio_path)
        print(f"   File size: {file_size} bytes")
        
        if file_size < 1000:
            print("⚠️  Warning: Audio file is very small, microphone may not be working")
            return False
        
        return audio_path
        
    except Exception as e:
        print(f"❌ Error recording audio: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_transcription(audio_path):
    """Test speech-to-text transcription."""
    print("\n=== Testing Speech-to-Text ===")
    try:
        print("Transcribing audio...")
        text = transcribe_audio(audio_path)
        
        if not text:
            print("❌ Transcription returned empty text")
            print("   This could mean:")
            print("   1. No speech was detected in the audio")
            print("   2. Microphone volume is too low")
            print("   3. Whisper model failed to load")
            return False
        
        print(f"✅ Transcription successful!")
        print(f"   Text: '{text}'")
        return True
        
    except Exception as e:
        print(f"❌ Error transcribing audio: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adaptive_recording():
    """Test adaptive recording (stops on silence)."""
    print("\n=== Testing Adaptive Recording ===")
    print("This will record until silence is detected...")
    print("Speak something within 2 seconds, then stop talking.")
    print("Starting in 2 seconds...")
    
    import time
    time.sleep(2)
    
    try:
        audio_path = record_audio_until_silence()
        
        if not audio_path:
            print("❌ Adaptive recording failed")
            return False
        
        print(f"✅ Adaptive recording successful: {audio_path}")
        
        # Try to transcribe
        text = transcribe_audio(audio_path)
        if text:
            print(f"   Transcribed: '{text}'")
        else:
            print("   (No speech detected)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in adaptive recording: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("VOICE MODULE DIAGNOSTIC TEST")
    print("=" * 60)
    
    # List devices
    list_audio_devices()
    
    # Test microphone
    audio_path = test_microphone()
    if not audio_path:
        print("\n❌ MICROPHONE TEST FAILED")
        print("\nPossible issues:")
        print("1. No microphone connected")
        print("2. Microphone permissions not granted")
        print("3. Wrong default audio device selected")
        print("\nTry:")
        print("- Check Windows Sound settings")
        print("- Grant microphone permissions")
        print("- Test microphone in Windows Voice Recorder")
        return
    
    # Test transcription
    if not test_transcription(audio_path):
        print("\n❌ TRANSCRIPTION TEST FAILED")
        print("\nPossible issues:")
        print("1. Whisper model not loaded")
        print("2. No speech in the recording")
        print("3. Audio quality too low")
        return
    
    # Test adaptive recording
    test_adaptive_recording()
    
    print("\n" + "=" * 60)
    print("✅ VOICE MODULE TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
