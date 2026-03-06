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
SILENCE_THRESHOLD = 350  # RMS threshold; below this triggers silence counter
SILENCE_DURATION = 1.5  # Seconds of silence before stopping recording
INITIAL_LISTEN_TIME = 2.0  # Wait up to 2 seconds for user to start speaking


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


def record_audio_until_silence(sample_rate: int = SAMPLE_RATE, 
                                max_duration: float = 30.0,
                                chunk_size: float = 0.1) -> str:
    """
    Record audio until silence is detected (proximity-favored).
    
    - Waits for user to start speaking (up to 2 seconds)
    - Continues recording while speech is detected
    - Stops when silence detected for ~1.5 seconds
    - Returns immediately for short commands
    - Allows longer messages as user speaks
    
    Args:
        sample_rate: Audio sampling rate
        max_duration: Maximum recording time (30 seconds default)
        chunk_size: Size of each audio chunk (0.1 seconds)
    
    Returns:
        Path to saved WAV file or empty string if failed
    """
    chunks = []
    total_time = 0.0
    silence_time = 0.0
    has_spoken = False
    chunk_frames = int(chunk_size * sample_rate)
    
    logger.info("[Recorder] Adaptive recording started - waiting for voice...")
    
    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
            while total_time < max_duration:
                # Read audio chunk
                data, _ = stream.read(chunk_frames)
                chunks.append(data.copy())
                total_time += chunk_size
                
                # Calculate RMS to detect speech
                rms = int(np.sqrt(np.mean(data.astype(np.float32) ** 2)))
                
                # Check if this is speech or silence
                if rms > SILENCE_THRESHOLD:
                    # Speech detected
                    has_spoken = True
                    silence_time = 0.0  # Reset silence counter
                    if total_time > 0.2:  # Don't log every chunk
                        logger.debug(f"[Recorder] Speech detected (RMS: {rms})")
                else:
                    # Silence detected
                    silence_time += chunk_size
                    
                    # If we've heard speech and now have extended silence, stop
                    if has_spoken and silence_time >= SILENCE_DURATION:
                        logger.info(f"[Recorder] Silence detected ({silence_time:.1f}s) - stopping recording")
                        break
                    
                    # If waiting for voice to start and time exceeded, stop
                    if not has_spoken and total_time >= INITIAL_LISTEN_TIME:
                        logger.warning(f"[Recorder] No speech detected in {INITIAL_LISTEN_TIME}s - stopping")
                        break
    
    except Exception as e:
        logger.error(f"[Recorder] Stream error: {e}")
        return ""
    
    if not chunks:
        logger.warning("[Recorder] No audio chunks captured")
        return ""
    
    # Concatenate all chunks
    audio = np.concatenate(chunks, axis=0)
    logger.info(f"[Recorder] Captured {total_time:.1f}s of adaptive audio")
    return _save_and_validate(audio, sample_rate)


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
