import sounddevice as sd
import scipy.io.wavfile as wav
import os
import uuid
import time
import tempfile
import numpy as np

from backend.config.logger import logger
from backend.config.settings import SAMPLE_RATE


MIN_AUDIO_LEVEL = 200  # RMS threshold; below this is considered silence


def record_audio_fixed(duration: float = 4.0, sample_rate: int = SAMPLE_RATE) -> str:
    """Record for a fixed duration (fallback)."""
    frames = int(duration * sample_rate)
    audio = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="int16")
    sd.wait()
    return _save_and_validate(audio, sample_rate)


def record_audio_while_held(key_check_fn, sample_rate: int = SAMPLE_RATE,
                            max_duration: float = 30.0, chunk_size: float = 0.1) -> str:
    """Record dynamically while key is held, stop when released."""
    chunks = []
    total = 0.0
    chunk_frames = int(chunk_size * sample_rate)

    logger.info("[Recorder] Dynamic recording started (speaking...)")

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
        while key_check_fn() and total < max_duration:
            data, _ = stream.read(chunk_frames)
            chunks.append(data.copy())
            total += chunk_size

    if not chunks:
        logger.warning("[Recorder] No audio chunks captured")
        return ""

    audio = np.concatenate(chunks, axis=0)
    logger.info(f"[Recorder] Captured {total:.1f}s of audio")
    return _save_and_validate(audio, sample_rate)


def record_audio(duration: float = 4.0, sample_rate: int = SAMPLE_RATE) -> str:
    """Default fixed-duration recording (kept for compatibility)."""
    return record_audio_fixed(duration, sample_rate)


def _save_and_validate(audio: np.ndarray, sample_rate: int) -> str:
    """Save audio array to temp WAV file and validate it has actual sound."""
    try:
        temp_dir = tempfile.gettempdir()
        filename = f"whisper_{uuid.uuid4().hex[:8]}.wav"
        temp_filepath = os.path.join(temp_dir, filename)

        wav.write(temp_filepath, sample_rate, audio)
        time.sleep(0.1)

        if not os.path.exists(temp_filepath):
            raise FileNotFoundError(f"Audio file not created at {temp_filepath}")

        # Audio level check — warn if silent
        rms = int(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))
        logger.info(f"[Recorder] Audio RMS level: {rms} (threshold: {MIN_AUDIO_LEVEL})")
        if rms < MIN_AUDIO_LEVEL:
            logger.warning("[Recorder] Audio appears SILENT — check microphone input device")

        file_size = os.path.getsize(temp_filepath)
        logger.info(f"[Recorder] Recording complete. File: {temp_filepath} ({file_size} bytes)")
        return temp_filepath

    except Exception as e:
        logger.error(f"[Recorder Error] {e}")
        raise
    
    except Exception as e:
        logger.error(f"[Recorder Error] {e}")
        import traceback
        logger.error(f"[Recorder Traceback] {traceback.format_exc()}")
        raise
