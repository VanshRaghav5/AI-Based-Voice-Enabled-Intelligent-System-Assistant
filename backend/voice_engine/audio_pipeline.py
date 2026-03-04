import keyboard
import time

from backend.voice_engine.input.recorder import record_audio_while_held
from backend.voice_engine.stt.whisper_engine import transcribe_audio
from backend.voice_engine.tts.tts_engine import speak_text
from backend.config.logger import logger


PUSH_TO_TALK_KEY = "space"
TEXT_INPUT_HOTKEY = "ctrl+t"


def listen() -> str:
    """
    SPACE = Push-to-talk (hold while speaking, release to transcribe)
    CTRL+T = Text input mode
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
            logger.info("Recording started (Push-to-Talk) — hold SPACE while speaking")

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
                logger.warning("[Pipeline] Empty transcription — speak clearly into microphone while holding SPACE")
                time.sleep(0.3)
                continue

            logger.info(f"Transcribed: {text}")
            return text.strip()


def speak(text: str):
    try:
        speak_text(text)
    except Exception as e:
        logger.error(f"[Voice Pipeline Error - Speak] {e}")
