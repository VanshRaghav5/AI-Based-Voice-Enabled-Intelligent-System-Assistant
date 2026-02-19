import keyboard
import time

from backend.voice_engine.input.recorder import record_audio
from backend.voice_engine.stt.whisper_engine import transcribe_audio
from backend.voice_engine.tts.tts_engine import speak_text
from backend.config.logger import logger


PUSH_TO_TALK_KEY = "space"
TEXT_INPUT_HOTKEY = "ctrl+t"


def listen() -> str:
    """
    SPACE = Push-to-talk
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
            logger.info("Recording started (Push-to-Talk)")

            audio_path = record_audio()

            logger.info("Recording finished. Transcribing...")
            text = transcribe_audio(audio_path)

            logger.info(f"Transcribed: {text}")
            return text.strip()


def speak(text: str):
    try:
        speak_text(text)
    except Exception as e:
        logger.error(f"[Voice Pipeline Error - Speak] {e}")
