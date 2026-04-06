import keyboard
import time

from backend.services.voice.input.recorder import record_audio_while_held, record_audio_fixed, record_audio_until_silence
from backend.utils.logger import logger
from backend.utils.settings import VOICE_ADAPTIVE_MAX_DURATION_SECONDS, VOICE_ADAPTIVE_CHUNK_SECONDS

try:
    from backend.services.voice.stt.faster_whisper_engine import transcribe_audio
    logger.info("[STT] Using faster-whisper engine")
except ModuleNotFoundError:
    from backend.services.voice.stt.whisper_engine import transcribe_audio
    logger.warning("[STT] faster-whisper not installed; falling back to whisper_engine")

from backend.services.voice.tts.tts_engine import speak_text


PUSH_TO_TALK_KEY = "space"
TEXT_INPUT_HOTKEY = "ctrl+t"
LISTENING_TIMEOUT = 5.0  # Record for up to 5 seconds in GUI mode


def listen() -> str:
    """
    SPACE = Push-to-talk (hold while speaking, release to transcribe)
    CTRL+T = Text input mode
    
    Note: For GUI mode, use listen_for_gui() instead
    """

    logger.info("Assistant ready. Hold SPACE to talk or press CTRL+T to type.")

    while True:

        # ---------- TEXT MODE ----------
        if keyboard.is_pressed(TEXT_INPUT_HOTKEY):
            time.sleep(0.3)  # allow key release
            logger.info("Text input mode activated.")
            print("\n--- TEXT MODE ---")
            text = input("Type your command: ")
            return text.strip()

        # ---------- PUSH TO TALK ----------
        if keyboard.is_pressed(PUSH_TO_TALK_KEY):
            logger.info("Recording started (Push-to-Talk) â€” hold SPACE while speaking")

            # Record dynamically while SPACE is held
            audio_path = record_audio_while_held(
                key_check_fn=lambda: keyboard.is_pressed(PUSH_TO_TALK_KEY)
            )

            if not audio_path:
                logger.warning("[Pipeline] No audio captured, skipping transcription")
                time.sleep(0.3)
                continue

            logger.info("Recording finished. Transcribing...")
            text = transcribe_audio(audio_path)

            if not text:
                logger.warning("[Pipeline] Empty transcription â€” speak clearly into microphone while holding SPACE")
                time.sleep(0.3)
                continue

            logger.info(f"Transcribed: {text}")
            return text.strip()


def listen_for_gui(duration: float = LISTENING_TIMEOUT) -> str:
    """
    Listen for voice input in GUI mode (non-blocking, fixed duration).
    
    This records audio for a fixed duration and returns the transcription.
    Designed for the desktop GUI where keyboard focus is not available.
    
    Args:
        duration: Recording duration in seconds (default: 5.0)
    
    Returns:
        Transcribed text or empty string if no speech detected
    """
    try:
        logger.info(f"[GUI Listen] Recording for {duration} seconds...")
        
        # Record audio for fixed duration
        audio_path = record_audio_fixed(duration=duration)
        
        if not audio_path:
            logger.warning("[GUI Listen] No audio captured")
            return ""
        
        logger.info("[GUI Listen] Recording finished. Transcribing...")
        text = transcribe_audio(audio_path)
        
        if not text:
            logger.warning("[GUI Listen] Empty transcription â€” speak clearly into microphone")
            return ""
        
        logger.info(f"[GUI Listen] Transcribed: {text}")
        return text.strip()
        
    except Exception as e:
        logger.error(f"[GUI Listen] Error: {e}", exc_info=True)
        return ""


def listen_for_gui_adaptive(should_stop=None) -> str:
    """
    Listen for voice input with ADAPTIVE/PROXIMITY-based duration.
    
    - Waits for user to start speaking (up to 2 seconds)
    - Continues recording while speech is detected  
    - Stops automatically when silence detected for ~1.5 seconds
    - Short commands finish quickly (great for UX)
    - Longer messages get full recording time as needed
    - Maximum recording time: 30 seconds
    
    Returns:
        Transcribed text or empty string if no speech detected
    """
    try:
        logger.info("[GUI Listen - Adaptive] Waiting for voice input...")
        
        # Record audio until silence is detected
        audio_path = record_audio_until_silence(
            max_duration=VOICE_ADAPTIVE_MAX_DURATION_SECONDS,
            chunk_size=VOICE_ADAPTIVE_CHUNK_SECONDS,
            should_stop=should_stop,
        )
        
        if not audio_path:
            logger.warning("[GUI Listen - Adaptive] No audio captured")
            return ""
        
        logger.info("[GUI Listen - Adaptive] Recording finished. Transcribing...")
        text = transcribe_audio(audio_path)
        
        if not text:
            logger.warning("[GUI Listen - Adaptive] Empty transcription â€” speak clearly into microphone")
            return ""
        
        logger.info(f"[GUI Listen - Adaptive] Transcribed: {text}")
        return text.strip()
        
    except Exception as e:
        logger.error(f"[GUI Listen - Adaptive] Error: {e}", exc_info=True)
        return ""


def speak(text: str, *, voice: str | None = None, accent: str | None = None):
    try:
        speak_text(text, voice=voice, accent=accent)
    except Exception as e:
        logger.error(f"[Voice Pipeline Error - Speak] {e}")
