import sounddevice as sd
import scipy.io.wavfile as wav
import os
import uuid

from backend.config.logger import logger
from backend.config.settings import RECORD_DURATION, SAMPLE_RATE


BASE_DIR = os.path.dirname(__file__)
BACKEND_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
AUDIO_DIR = os.path.join(BACKEND_ROOT, "data", "audio")


def record_audio(duration=RECORD_DURATION, sample_rate=SAMPLE_RATE) -> str:
    """
    Fixed-duration audio recording.
    """

    os.makedirs(AUDIO_DIR, exist_ok=True)

    filename = f"{uuid.uuid4()}.wav"
    filepath = os.path.join(AUDIO_DIR, filename)

    logger.info("Recording started")

    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    wav.write(filepath, sample_rate, audio)

    logger.info("Recording complete")

    return filepath
