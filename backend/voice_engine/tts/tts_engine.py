import subprocess
import os
import uuid
import sys

# ---------- BASE PATHS ----------
BASE_DIR = os.path.dirname(__file__)
BACKEND_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
AUDIO_OUTPUT_DIR = os.path.join(BACKEND_ROOT, "data", "audio")

PIPER_DIR = os.path.join(BASE_DIR, "piper")
PIPER_EXE = os.path.join(PIPER_DIR, "piper.exe")

VOICE_MODEL = os.path.join(PIPER_DIR, "en_US-danny-low.onnx")
VOICE_CONFIG = os.path.join(PIPER_DIR, "en_US-danny-low.onnx.json")
ESPEAK_DATA = os.path.join(PIPER_DIR, "espeak-ng-data")

os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)

# ---------- VOICE TUNING ----------
LENGTH_SCALE = "1.4"
NOISE_SCALE = "0.667"
NOISE_W = "0.8"


def speak_text(text: str) -> str:
    """
    Converts text to speech using Piper.
    Returns generated audio file path.
    """

    if not os.path.exists(PIPER_EXE):
        print("[TTS Error] Piper executable not found.")
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
            "--length_scale", LENGTH_SCALE,
            "--noise_scale", NOISE_SCALE,
            "--noise_w", NOISE_W
        ]

        subprocess.run(
            command,
            cwd=PIPER_DIR,
            input=text,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30  # prevent hanging
        )

        # Play audio (Windows-safe)
        if sys.platform.startswith("win"):
            os.startfile(output_file)
        else:
            print("Audio generated at:", output_file)

        return output_file

    except subprocess.TimeoutExpired:
        print("[TTS Error] Piper timed out.")
        return ""

    except Exception as e:
        print(f"[TTS Error] {e}")
        return ""
