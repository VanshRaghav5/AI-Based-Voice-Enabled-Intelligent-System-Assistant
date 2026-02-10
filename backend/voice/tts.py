import subprocess
import os
import uuid

BASE_DIR = os.path.dirname(__file__)
PIPER_DIR = os.path.join(BASE_DIR, "piper")

PIPER_EXE = os.path.join(PIPER_DIR, "piper.exe")
VOICE_MODEL = os.path.join(PIPER_DIR, "en_US-danny-low.onnx")
VOICE_CONFIG = os.path.join(PIPER_DIR, "en_US-danny-low.onnx.json")
ESPEAK_DATA = os.path.join(PIPER_DIR, "espeak-ng-data")

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🎚️ Voice tuning
LENGTH_SCALE = "1.4"   # slower, assistant-like
NOISE_SCALE = "0.667"
NOISE_W = "0.8"


def speak(text: str) -> str:
    """
    Converts text to speech using Piper.
    """
    output_file = os.path.join(OUTPUT_DIR, f"{uuid.uuid4()}.wav")

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
        stderr=subprocess.DEVNULL
    )

    # Play audio (Windows)
    os.system(f'start "" "{output_file}"')
    return output_file
