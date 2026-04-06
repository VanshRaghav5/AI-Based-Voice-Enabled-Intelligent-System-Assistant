"""
faster-whisper STT engine â€” drop-in replacement for whisper_engine.py

Key improvements over openai-whisper:
  - 4-8x faster inference via CTranslate2 (int8 quantization on CPU)
  - Built-in VAD filter suppresses silence/hallucinations automatically
  - Correct handling of int16 / int32 / float32 WAV dtypes
  - Auto-resamples audio to the required 16 kHz if mic records at a different rate
  - Same public API: transcribe_audio(audio_path) -> str
"""

import os
import re
import threading
import time

import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal
import torch

from faster_whisper import WhisperModel

from backend.utils.logger import logger
from backend.utils.settings import (
    WHISPER_MODEL,
    WHISPER_LANGUAGE,
    WHISPER_BEAM_SIZE,
    WHISPER_NO_SPEECH_THRESHOLD,
    WHISPER_LOG_PROB_THRESHOLD,
    WHISPER_COMPRESSION_RATIO_THRESHOLD,
    WHISPER_MIN_AUDIO_RMS,
    WHISPER_VAD_MIN_SILENCE_MS,
    WHISPER_MAX_AUDIO_SECONDS,
    WHISPER_INITIAL_PROMPT,
    WHISPER_TEXT_CORRECTIONS,
    FASTER_WHISPER_COMPUTE_TYPE,
    WHISPER_ENABLE_DENOISE,
    WHISPER_DENOISE_NOISE_PERCENTILE,
    WHISPER_DENOISE_GATE_MULTIPLIER,
    WHISPER_PREEMPHASIS_ALPHA,
    WHISPER_NORMALIZE_TARGET_PEAK,
)


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
WHISPER_SAMPLE_RATE = 16000

_current_device = DEVICE
_current_compute_type = FASTER_WHISPER_COMPUTE_TYPE

logger.info(f"faster-whisper running on: {DEVICE} / compute_type={FASTER_WHISPER_COMPUTE_TYPE}")

model: WhisperModel | None = None
_model_lock = threading.Lock()


def load_whisper_model() -> WhisperModel | None:
    """Load and cache the faster-whisper model."""
    global model, _current_device, _current_compute_type
    try:
        model = WhisperModel(
            WHISPER_MODEL,
            device=_current_device,
            compute_type=_current_compute_type,
        )
        logger.info(
            f"faster-whisper '{WHISPER_MODEL}' loaded successfully "
            f"({_current_device}/{_current_compute_type})"
        )
    except Exception as e:
        logger.error(f"[faster-whisper Load Error] {e}")
        model = None
    return model


def _to_float32_mono(audio_data: np.ndarray, sample_rate: int) -> tuple[np.ndarray, int]:
    """Convert raw WAV data to float32 mono at 16 kHz."""
    # --- dtype normalisation ---
    if audio_data.dtype == np.int16:
        audio_float = audio_data.astype(np.float32) / 32768.0
    elif audio_data.dtype == np.int32:
        audio_float = audio_data.astype(np.float32) / 2_147_483_648.0
    elif audio_data.dtype == np.uint8:
        audio_float = (audio_data.astype(np.float32) - 128.0) / 128.0
    elif audio_data.dtype in (np.float32, np.float64):
        audio_float = audio_data.astype(np.float32)
    else:
        audio_float = audio_data.astype(np.float32) / 32768.0

    # --- stereo â†’ mono ---
    if audio_float.ndim == 2:
        audio_float = audio_float.mean(axis=1)

    # --- resample to 16 kHz if needed ---
    if sample_rate != WHISPER_SAMPLE_RATE:
        gcd = _gcd(sample_rate, WHISPER_SAMPLE_RATE)
        up = WHISPER_SAMPLE_RATE // gcd
        down = sample_rate // gcd
        audio_float = signal.resample_poly(audio_float, up, down).astype(np.float32)
        logger.info(
            f"[faster-whisper] Resampled audio from {sample_rate} Hz â†’ {WHISPER_SAMPLE_RATE} Hz"
        )
        sample_rate = WHISPER_SAMPLE_RATE

    return audio_float, sample_rate


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def _apply_text_corrections(text: str) -> str:
    """Apply configurable, case-insensitive whole-word transcript corrections."""
    if not text:
        return ""
    corrected = re.sub(r"\s+", " ", text).strip()
    for wrong, right in WHISPER_TEXT_CORRECTIONS.items():
        pattern = r"\b" + re.escape(wrong) + r"\b"
        updated = re.sub(pattern, right, corrected, flags=re.IGNORECASE)
        if updated != corrected:
            logger.info(f"[faster-whisper] Correction: '{wrong}' â†’ '{right}'")
            corrected = updated
    return corrected


def _rms_level(audio_float: np.ndarray) -> float:
    if audio_float.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(audio_float, dtype=np.float32))))


def _filter_low_confidence_text(
    segments_list: list,
    text: str,
    *,
    log_prefix: str,
    log_prob_threshold: float,
) -> str:
    if not text:
        return ""
    if not segments_list:
        return ""

    avg_logprob_values = [float(getattr(seg, "avg_logprob", -10.0)) for seg in segments_list]
    avg_logprob = float(np.mean(avg_logprob_values)) if avg_logprob_values else -10.0

    if avg_logprob < log_prob_threshold:
        logger.warning(
            f"{log_prefix} Dropping low-confidence transcript "
            f"(avg_logprob={avg_logprob:.3f}, threshold={log_prob_threshold})"
        )
        return ""

    return text


def _clip_audio_for_commands(audio_float: np.ndarray, log_prefix: str) -> np.ndarray:
    """Cap very long command audio to keep response latency predictable."""
    max_samples = int(WHISPER_MAX_AUDIO_SECONDS * WHISPER_SAMPLE_RATE)
    if audio_float.size > max_samples > 0:
        logger.info(
            f"{log_prefix} Clipping audio from {audio_float.size / WHISPER_SAMPLE_RATE:.2f}s "
            f"to {WHISPER_MAX_AUDIO_SECONDS:.2f}s for realtime command processing"
        )
        return audio_float[:max_samples]
    return audio_float


def _preprocess_for_noise(audio_float: np.ndarray) -> np.ndarray:
    """Apply lightweight denoise, pre-emphasis, and peak normalization."""
    if audio_float.size == 0:
        return audio_float

    processed = np.asarray(audio_float, dtype=np.float32)
    processed = processed - float(np.mean(processed))

    if WHISPER_ENABLE_DENOISE:
        percentile = float(np.clip(WHISPER_DENOISE_NOISE_PERCENTILE, 1.0, 50.0))
        gate_multiplier = max(1.0, float(WHISPER_DENOISE_GATE_MULTIPLIER))
        noise_floor = float(np.percentile(np.abs(processed), percentile))
        noise_gate = max(noise_floor * gate_multiplier, 1e-5)
        processed = np.where(np.abs(processed) < noise_gate, 0.0, processed)

    preemphasis_alpha = float(np.clip(WHISPER_PREEMPHASIS_ALPHA, 0.0, 0.99))
    if preemphasis_alpha > 0.0 and processed.size > 1:
        emphasized = np.empty_like(processed)
        emphasized[0] = processed[0]
        emphasized[1:] = processed[1:] - (preemphasis_alpha * processed[:-1])
        processed = emphasized

    target_peak = float(np.clip(WHISPER_NORMALIZE_TARGET_PEAK, 0.1, 1.0))
    peak = float(np.max(np.abs(processed))) if processed.size else 0.0
    if peak > 1e-8:
        processed = (processed / peak) * target_peak

    return np.clip(processed, -1.0, 1.0).astype(np.float32)


# Model is loaded lazily on first transcription call â€” backend starts instantly.
# Call load_whisper_model() explicitly if you need pre-warming at startup.
_model_load_attempted = False


def _is_cuda_runtime_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "cublas" in msg
        or "cudnn" in msg
        or "cuda" in msg
        or "cannot be loaded" in msg
    )


def _fallback_to_cpu_model(log_prefix: str) -> bool:
    """Fallback model backend from CUDA to CPU when CUDA runtime libs are missing."""
    global model, _current_device, _current_compute_type

    if _current_device == "cpu":
        return False

    logger.warning(f"{log_prefix} CUDA runtime unavailable. Falling back to CPU model.")
    _current_device = "cpu"
    _current_compute_type = "int8"
    model = None
    return _ensure_model_loaded(force_reload=True)


def _ensure_model_loaded(force_reload: bool = False) -> bool:
    """Load model on first use; block until ready to avoid first-call empty transcriptions."""
    global model, _model_load_attempted

    if force_reload:
        _model_load_attempted = False

    if model is not None:
        return True

    with _model_lock:
        if model is not None:
            return True
        if not _model_load_attempted or force_reload:
            _model_load_attempted = True
            load_whisper_model()

    return model is not None


def transcribe_numpy(
    audio_float: np.ndarray,
    sample_rate: int = WHISPER_SAMPLE_RATE,
    *,
    language_override: str | None = None,
    initial_prompt_override: str | None = None,
    apply_corrections: bool = True,
    min_audio_rms_override: float | None = None,
    log_prob_threshold_override: float | None = None,
    log_prefix: str = "[faster-whisper]",
) -> str:
    """
    Transcribe audio directly from a numpy float32 array â€” no disk I/O.

    This is the zero-latency path: the recorder hands over the numpy array
    immediately after speech ends, so no WAV write/read roundtrip occurs.

    Args:
        audio_float: Mono or stereo float32 audio (any sample rate).
        sample_rate: Sample rate of the input array (resampled to 16 kHz if needed).
        Other args same as transcribe_audio().
    """
    if not _ensure_model_loaded():
        logger.error("[faster-whisper] Model not loaded.")
        return ""

    try:
        # Normalise dtype + channels + sample rate
        audio_float, _ = _to_float32_mono(audio_float, sample_rate)
        audio_float = _clip_audio_for_commands(audio_float, log_prefix)
        audio_float = _preprocess_for_noise(audio_float)

        min_audio_rms = (
            min_audio_rms_override
            if min_audio_rms_override is not None
            else WHISPER_MIN_AUDIO_RMS
        )
        log_prob_threshold = (
            log_prob_threshold_override
            if log_prob_threshold_override is not None
            else WHISPER_LOG_PROB_THRESHOLD
        )

        rms = _rms_level(audio_float)
        if rms < min_audio_rms:
            logger.warning(
                f"{log_prefix} Audio RMS below threshold "
                f"({rms:.5f} < {min_audio_rms})"
            )
            return ""

        if len(audio_float) < WHISPER_SAMPLE_RATE * 0.3:
            logger.warning(f"{log_prefix} Audio too short, skipping.")
            return ""

        language = language_override if language_override is not None else WHISPER_LANGUAGE
        initial_prompt = (
            initial_prompt_override
            if initial_prompt_override is not None
            else WHISPER_INITIAL_PROMPT
        ) or None

        t0 = time.perf_counter()
        segments, info = model.transcribe(
            audio_float,
            beam_size=WHISPER_BEAM_SIZE,
            language=language,
            initial_prompt=initial_prompt,
            no_speech_threshold=WHISPER_NO_SPEECH_THRESHOLD,
            log_prob_threshold=log_prob_threshold,
            compression_ratio_threshold=WHISPER_COMPRESSION_RATIO_THRESHOLD,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": WHISPER_VAD_MIN_SILENCE_MS},
            condition_on_previous_text=False,
            temperature=0.0,
        )

        segments_list = list(segments)
        logger.info(f"{log_prefix} Decode completed in {time.perf_counter() - t0:.2f}s")
        text = "".join(seg.text for seg in segments_list).strip()
        text = _filter_low_confidence_text(
            segments_list,
            text,
            log_prefix=log_prefix,
            log_prob_threshold=log_prob_threshold,
        )
        if apply_corrections:
            text = _apply_text_corrections(text)

        logger.info(
            f"{log_prefix} Result (lang={info.language}, p={info.language_probability:.2f}): {text}"
        )
        return text

    except Exception as e:
        if _is_cuda_runtime_error(e) and _fallback_to_cpu_model(log_prefix):
            logger.info(f"{log_prefix} Retrying transcription on CPU backend")
            return transcribe_numpy(
                audio_float,
                sample_rate,
                language_override=language_override,
                initial_prompt_override=initial_prompt_override,
                apply_corrections=apply_corrections,
                min_audio_rms_override=min_audio_rms_override,
                log_prob_threshold_override=log_prob_threshold_override,
                log_prefix=log_prefix,
            )
        import traceback
        logger.error(f"{log_prefix} Transcription error: {e}")
        logger.error(f"{log_prefix} {traceback.format_exc()}")
        return ""


def transcribe_audio(
    audio_path: str,
    *,
    language_override: str | None = None,
    initial_prompt_override: str | None = None,
    apply_corrections: bool = True,
    min_audio_rms_override: float | None = None,
    log_prob_threshold_override: float | None = None,
    log_prefix: str = "[faster-whisper]",
) -> str:
    """
    Transcribe a WAV file to text.

    Drop-in replacement for whisper_engine.transcribe_audio â€” identical signature.

    Args:
        audio_path: Path to a WAV file.
        language_override: ISO-639-1 language code (overrides settings).
        initial_prompt_override: Custom initial prompt (overrides settings).
        apply_corrections: Whether to run text corrections.
        log_prefix: Logging prefix for messages.

    Returns:
        Transcribed text or empty string on failure.
    """
    if not _ensure_model_loaded():
        logger.error("[faster-whisper] Model not loaded.")
        return ""

    try:
        # --- resolve audio path ---
        if not audio_path or not os.path.exists(audio_path):
            abs_path = os.path.abspath(audio_path)
            if os.path.exists(abs_path):
                audio_path = abs_path
            else:
                logger.error(f"{log_prefix} Audio file not found: {audio_path}")
                return ""

        file_size = os.path.getsize(audio_path)
        logger.info(f"{log_prefix} Transcribing: {audio_path} ({file_size} bytes)")

        # --- load & preprocess ---
        sample_rate, audio_data = wavfile.read(audio_path)
        audio_float, _ = _to_float32_mono(audio_data, sample_rate)
        audio_float = _clip_audio_for_commands(audio_float, log_prefix)
        audio_float = _preprocess_for_noise(audio_float)

        min_audio_rms = (
            min_audio_rms_override
            if min_audio_rms_override is not None
            else WHISPER_MIN_AUDIO_RMS
        )
        log_prob_threshold = (
            log_prob_threshold_override
            if log_prob_threshold_override is not None
            else WHISPER_LOG_PROB_THRESHOLD
        )

        rms = _rms_level(audio_float)
        if rms < min_audio_rms:
            logger.warning(
                f"{log_prefix} Audio RMS below threshold "
                f"({rms:.5f} < {min_audio_rms})"
            )
            return ""

        # --- silence guard: skip clips that are too short ---
        if len(audio_float) < WHISPER_SAMPLE_RATE * 0.3:
            logger.warning(f"{log_prefix} Audio too short ({len(audio_float)} samples), skipping.")
            return ""

        # --- language ---
        language = language_override if language_override is not None else WHISPER_LANGUAGE

        # --- initial prompt ---
        initial_prompt = (
            initial_prompt_override
            if initial_prompt_override is not None
            else WHISPER_INITIAL_PROMPT
        ) or None  # faster-whisper wants None, not ""

        # --- transcribe ---
        t0 = time.perf_counter()
        segments, info = model.transcribe(
            audio_float,
            beam_size=WHISPER_BEAM_SIZE,
            language=language,
            initial_prompt=initial_prompt,
            no_speech_threshold=WHISPER_NO_SPEECH_THRESHOLD,
            log_prob_threshold=log_prob_threshold,
            compression_ratio_threshold=WHISPER_COMPRESSION_RATIO_THRESHOLD,
            vad_filter=True,          # skip silent regions â†’ fewer hallucinations
            vad_parameters={"min_silence_duration_ms": WHISPER_VAD_MIN_SILENCE_MS},
            condition_on_previous_text=False,
            temperature=0.0,
        )

        # segments is a generator â€” consume it
        segments_list = list(segments)
        logger.info(f"{log_prefix} Decode completed in {time.perf_counter() - t0:.2f}s")
        text = "".join(seg.text for seg in segments_list).strip()
        text = _filter_low_confidence_text(
            segments_list,
            text,
            log_prefix=log_prefix,
            log_prob_threshold=log_prob_threshold,
        )

        if apply_corrections:
            text = _apply_text_corrections(text)

        logger.info(f"{log_prefix} Result (lang={info.language}, p={info.language_probability:.2f}): {text}")
        return text

    except FileNotFoundError as e:
        logger.error(f"{log_prefix} File not found: {audio_path} â€” {e}")
        return ""
    except Exception as e:
        if _is_cuda_runtime_error(e) and _fallback_to_cpu_model(log_prefix):
            logger.info(f"{log_prefix} Retrying transcription on CPU backend")
            return transcribe_audio(
                audio_path,
                language_override=language_override,
                initial_prompt_override=initial_prompt_override,
                apply_corrections=apply_corrections,
                min_audio_rms_override=min_audio_rms_override,
                log_prob_threshold_override=log_prob_threshold_override,
                log_prefix=log_prefix,
            )
        import traceback
        logger.error(f"{log_prefix} Transcription error: {e}")
        logger.error(f"{log_prefix} {traceback.format_exc()}")
        return ""
