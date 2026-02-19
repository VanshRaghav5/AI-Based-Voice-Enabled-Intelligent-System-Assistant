import subprocess
import os
import uuid
import sounddevice as sd
import scipy.io.wavfile as wav

from backend.config.settings import (
    TTS_LENGTH_SCALE,
    TTS_NOISE_SCALE,
    TTS_NOISE_W
)
from backend.config.logger import logger


BASE_DIR = os.path.dirname(__file__)
BACKEND_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
AUDIO_OUTPUT_DIR = os.path.join(BACKEND_ROOT, "data", "audio")

PIPER_DIR = os.path.join(BASE_DIR, "piper")
PIPER_EXE = os.path.join(PIPER_DIR, "piper.exe")

VOICE_MODEL = os.path.join(PIPER_DIR, "en_US-danny-low.onnx")
VOICE_CONFIG = os.path.join(PIPER_DIR, "en_US-danny-low.onnx.json")
ESPEAK_DATA = os.path.join(PIPER_DIR, "espeak-ng-data")

os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)


def speak_text(text: str) -> str:

    if not os.path.exists(PIPER_EXE):
        logger.error("[TTS Error] Piper executable not found.")
        return ""

    try:
        output_file = os.path.join(
            AUDIO_OUTPUT_DIR,
            f"{uuid.uuid4()}.wav"
        )

        command = [
            PIPER_EXE,
            "--model", VOICE_MODEL,
            "--config", VOICE_CONFIG,
            "--output_file", output_file,
            "--espeak_data", ESPEAK_DATA,
            "--length_scale", str(TTS_LENGTH_SCALE),
            "--noise_scale", str(TTS_NOISE_SCALE),
            "--noise_w", str(TTS_NOISE_W)
        ]

        logger.info("Running Piper TTS...")

        subprocess.run(
            command,
            cwd=PIPER_DIR,
            input=text,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30
        )

        rate, audio = wav.read(output_file)
        sd.play(audio, rate)
        sd.wait()

        os.remove(output_file)

        logger.info("TTS playback completed")

        return "success"

    except subprocess.TimeoutExpired:
        logger.error("[TTS Error] Piper timed out.")
        return ""

    except Exception as e:
        logger.error(f"[TTS Error] {e}")
        return ""
