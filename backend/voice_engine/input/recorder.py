import sounddevice as sd
import scipy.io.wavfile as wav
import os
import uuid
import time
import tempfile
import numpy as np

from backend.config.logger import logger
from backend.config.settings import (
    SAMPLE_RATE,
    RECORDING_INPUT_DEVICE,
    RECORDING_MIN_AUDIO_LEVEL,
    RECORDING_NOISE_CALIBRATION_SECONDS,
    RECORDING_DYNAMIC_SILENCE_MULTIPLIER,
    RECORDING_DYNAMIC_SILENCE_MIN,
    RECORDING_DYNAMIC_SILENCE_MAX,
    RECORDING_SILENCE_DURATION_SECONDS,
    RECORDING_INITIAL_LISTEN_SECONDS,
)


MIN_AUDIO_LEVEL = RECORDING_MIN_AUDIO_LEVEL  # RMS threshold; below this is considered silence
SILENCE_THRESHOLD = max(140, int(MIN_AUDIO_LEVEL * 2))  # Speech gate tuned for typical laptop mic RMS
SILENCE_DURATION = max(0.3, float(RECORDING_SILENCE_DURATION_SECONDS))
INITIAL_LISTEN_TIME = max(0.6, float(RECORDING_INITIAL_LISTEN_SECONDS))

_INPUT_DEVICE_LOGGED = False


def _input_kwargs() -> dict:
    """Resolve optional input device setting for sounddevice APIs."""
    global _INPUT_DEVICE_LOGGED
    if RECORDING_INPUT_DEVICE in (None, "", "default"):
        return {}

    device = RECORDING_INPUT_DEVICE
    if isinstance(device, str):
        stripped = device.strip()
        if stripped.isdigit():
            device = int(stripped)
        else:
            device = stripped

    if not _INPUT_DEVICE_LOGGED:
        logger.info(f"[Recorder] Using configured input device: {device}")
        _INPUT_DEVICE_LOGGED = True

    return {"device": device}


def _trim_silence(audio: np.ndarray, threshold: int = SILENCE_THRESHOLD) -> np.ndarray:
    """Trim low-energy leading/trailing regions to reduce STT hallucinations."""
    if audio.size == 0:
        return audio

    mono = audio.reshape(-1) if audio.ndim > 1 else audio
    energy_idx = np.where(np.abs(mono.astype(np.int32)) > int(threshold * 0.6))[0]

    if energy_idx.size == 0:
        return np.array([], dtype=audio.dtype)

    start = int(energy_idx[0])
    end = int(energy_idx[-1]) + 1
    return audio[start:end]


def _compute_dynamic_silence_threshold(noise_floor_rms: float) -> int:
    """Adapt speech gate to room noise while keeping safe bounds."""
    scaled = int(noise_floor_rms * RECORDING_DYNAMIC_SILENCE_MULTIPLIER)
    baseline = max(SILENCE_THRESHOLD, scaled)
    return int(np.clip(baseline, RECORDING_DYNAMIC_SILENCE_MIN, RECORDING_DYNAMIC_SILENCE_MAX))


def record_audio_fixed(
    duration: float = 4.0,
    sample_rate: int = SAMPLE_RATE,
    *,
    warn_on_silence: bool = True,
) -> str:
    """Record for a fixed duration (fallback)."""
    frames = int(duration * sample_rate)
    audio = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="int16", **_input_kwargs())
    sd.wait()
    return _save_and_validate(audio, sample_rate, warn_on_silence=warn_on_silence)


def record_audio_while_held(key_check_fn, sample_rate: int = SAMPLE_RATE,
                            max_duration: float = 30.0, chunk_size: float = 0.1,
                            *, warn_on_silence: bool = True) -> str:
    """Record dynamically while key is held, stop when released."""
    chunks = []
    total = 0.0
    chunk_frames = int(chunk_size * sample_rate)

    logger.info("[Recorder] Dynamic recording started (speaking...)")

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16", **_input_kwargs()) as stream:
        while key_check_fn() and total < max_duration:
            data, _ = stream.read(chunk_frames)
            chunks.append(data.copy())
            total += chunk_size

    if not chunks:
        logger.warning("[Recorder] No audio chunks captured")
        return ""

    audio = np.concatenate(chunks, axis=0)
    logger.info(f"[Recorder] Captured {total:.1f}s of audio")
    return _save_and_validate(audio, sample_rate, warn_on_silence=warn_on_silence)


def record_audio(duration: float = 4.0, sample_rate: int = SAMPLE_RATE) -> str:
    """Default fixed-duration recording (kept for compatibility)."""
    return record_audio_fixed(duration, sample_rate)


def record_audio_until_silence(sample_rate: int = SAMPLE_RATE, 
                                max_duration: float = 30.0,
                                chunk_size: float = 0.1,
                                should_stop=None) -> str:
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
    ended_without_speech = False
    dynamic_threshold = SILENCE_THRESHOLD
    noise_floor_rms = float(SILENCE_THRESHOLD // 2)
    noise_calibration_window = max(0.0, RECORDING_NOISE_CALIBRATION_SECONDS)
    chunk_frames = int(chunk_size * sample_rate)
    
    logger.info("[Recorder] Adaptive recording started - waiting for voice...")
    
    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16", **_input_kwargs()) as stream:
            while total_time < max_duration:
                if callable(should_stop) and should_stop():
                    logger.info("[Recorder] Stop requested externally - ending recording")
                    break

                # Read audio chunk
                data, _ = stream.read(chunk_frames)
                chunks.append(data.copy())
                total_time += chunk_size
                
                # Calculate RMS to detect speech
                rms = int(np.sqrt(np.mean(data.astype(np.float32) ** 2)))

                # Calibrate ambient noise floor at session start.
                if not has_spoken:
                    should_update_noise_floor = (
                        total_time <= noise_calibration_window
                        or rms <= int(noise_floor_rms * 1.8)
                    )
                    if should_update_noise_floor:
                        noise_floor_rms = (0.85 * noise_floor_rms) + (0.15 * float(rms))
                    dynamic_threshold = _compute_dynamic_silence_threshold(noise_floor_rms)
                
                # Check if this is speech or silence
                if rms > dynamic_threshold:
                    # Speech detected
                    has_spoken = True
                    silence_time = 0.0  # Reset silence counter
                    if total_time > 0.2:  # Don't log every chunk
                        logger.debug(
                            f"[Recorder] Speech detected (RMS: {rms}, threshold: {dynamic_threshold})"
                        )
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
                        ended_without_speech = True
                        break
    
    except Exception as e:
        logger.error(f"[Recorder] Stream error: {e}")
        return ""
    
    if not chunks:
        logger.warning("[Recorder] No audio chunks captured")
        return ""

    if ended_without_speech and not has_spoken:
        logger.debug("[Recorder] Exiting adaptive capture without speech")
        return ""
    
    # Concatenate all chunks
    audio = np.concatenate(chunks, axis=0)
    audio = _trim_silence(audio, threshold=dynamic_threshold)
    if audio.size == 0:
        logger.warning("[Recorder] Audio was only silence after trimming")
        return ""

    logger.info(f"[Recorder] Captured {total_time:.1f}s of adaptive audio")
    return _save_and_validate(audio, sample_rate)


def _save_and_validate(audio: np.ndarray, sample_rate: int, *, warn_on_silence: bool = True) -> str:
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
            if warn_on_silence:
                logger.warning("[Recorder] Audio appears SILENT — check microphone input device")
            else:
                logger.debug("[Recorder] Wake-word chunk below speech threshold")

        file_size = os.path.getsize(temp_filepath)
        logger.info(f"[Recorder] Recording complete. File: {temp_filepath} ({file_size} bytes)")
        return temp_filepath

    except Exception as e:
        logger.error(f"[Recorder Error] {e}")
        import traceback
        logger.error(f"[Recorder Traceback] {traceback.format_exc()}")
        raise
