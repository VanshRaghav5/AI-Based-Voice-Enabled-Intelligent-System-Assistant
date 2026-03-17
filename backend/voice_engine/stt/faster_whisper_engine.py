"""
faster-whisper STT engine — drop-in replacement for whisper_engine.py

Key improvements over openai-whisper:
  - 4-8x faster inference via CTranslate2 (int8 quantization on CPU)
  - Built-in VAD filter suppresses silence/hallucinations automatically
  - Correct handling of int16 / int32 / float32 WAV dtypes
  - Auto-resamples audio to the required 16 kHz if mic records at a different rate
  - Same public API: transcribe_audio(audio_path) -> str
"""

import os
import re

import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal
import torch

from faster_whisper import WhisperModel

from backend.config.logger import logger
from backend.config.settings import (
    WHISPER_MODEL,
    WHISPER_LANGUAGE,
    WHISPER_BEAM_SIZE,
    WHISPER_NO_SPEECH_THRESHOLD,
    WHISPER_INITIAL_PROMPT,
    WHISPER_TEXT_CORRECTIONS,
    FASTER_WHISPER_COMPUTE_TYPE,
)


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
WHISPER_SAMPLE_RATE = 16000

logger.info(f"faster-whisper running on: {DEVICE} / compute_type={FASTER_WHISPER_COMPUTE_TYPE}")

model: WhisperModel | None = None


def load_whisper_model() -> WhisperModel | None:
    """Load and cache the faster-whisper model."""
    global model
    try:
        model = WhisperModel(
            WHISPER_MODEL,
            device=DEVICE,
            compute_type=FASTER_WHISPER_COMPUTE_TYPE,
        )
        logger.info(
            f"faster-whisper '{WHISPER_MODEL}' loaded successfully "
            f"({DEVICE}/{FASTER_WHISPER_COMPUTE_TYPE})"
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

    # --- stereo → mono ---
    if audio_float.ndim == 2:
        audio_float = audio_float.mean(axis=1)

    # --- resample to 16 kHz if needed ---
    if sample_rate != WHISPER_SAMPLE_RATE:
        gcd = _gcd(sample_rate, WHISPER_SAMPLE_RATE)
        up = WHISPER_SAMPLE_RATE // gcd
        down = sample_rate // gcd
        audio_float = signal.resample_poly(audio_float, up, down).astype(np.float32)
        logger.info(
            f"[faster-whisper] Resampled audio from {sample_rate} Hz → {WHISPER_SAMPLE_RATE} Hz"
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
            logger.info(f"[faster-whisper] Correction: '{wrong}' → '{right}'")
            corrected = updated
    return corrected


# Model is loaded lazily on first transcription call — backend starts instantly.
# Call load_whisper_model() explicitly if you need pre-warming at startup.
_model_load_attempted = False


def _ensure_model_loaded() -> None:
    """Load the model once on first use (lazy init)."""
    global model, _model_load_attempted
    if model is None and not _model_load_attempted:
        _model_load_attempted = True
        import threading
        threading.Thread(target=load_whisper_model, daemon=True, name="whisper-loader").start()


def transcribe_numpy(
    audio_float: np.ndarray,
    sample_rate: int = WHISPER_SAMPLE_RATE,
    *,
    language_override: str | None = None,
    initial_prompt_override: str | None = None,
    apply_corrections: bool = True,
    log_prefix: str = "[faster-whisper]",
) -> str:
    """
    Transcribe audio directly from a numpy float32 array — no disk I/O.

    This is the zero-latency path: the recorder hands over the numpy array
    immediately after speech ends, so no WAV write/read roundtrip occurs.

    Args:
        audio_float: Mono or stereo float32 audio (any sample rate).
        sample_rate: Sample rate of the input array (resampled to 16 kHz if needed).
        Other args same as transcribe_audio().
    """
    _ensure_model_loaded()
    if model is None:
        logger.error("[faster-whisper] Model not loaded.")
        return ""

    try:
        # Normalise dtype + channels + sample rate
        audio_float, _ = _to_float32_mono(audio_float, sample_rate)

        if len(audio_float) < WHISPER_SAMPLE_RATE * 0.3:
            logger.warning(f"{log_prefix} Audio too short, skipping.")
            return ""

        language = language_override if language_override is not None else WHISPER_LANGUAGE
        initial_prompt = (
            initial_prompt_override
            if initial_prompt_override is not None
            else WHISPER_INITIAL_PROMPT
        ) or None

        segments, info = model.transcribe(
            audio_float,
            beam_size=WHISPER_BEAM_SIZE,
            language=language,
            initial_prompt=initial_prompt,
            no_speech_threshold=WHISPER_NO_SPEECH_THRESHOLD,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
            condition_on_previous_text=False,
            temperature=0.0,
        )

        text = "".join(seg.text for seg in segments).strip()
        if apply_corrections:
            text = _apply_text_corrections(text)

        logger.info(
            f"{log_prefix} Result (lang={info.language}, p={info.language_probability:.2f}): {text}"
        )
        return text

    except Exception as e:
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
    log_prefix: str = "[faster-whisper]",
) -> str:
    """
    Transcribe a WAV file to text.

    Drop-in replacement for whisper_engine.transcribe_audio — identical signature.

    Args:
        audio_path: Path to a WAV file.
        language_override: ISO-639-1 language code (overrides settings).
        initial_prompt_override: Custom initial prompt (overrides settings).
        apply_corrections: Whether to run text corrections.
        log_prefix: Logging prefix for messages.

    Returns:
        Transcribed text or empty string on failure.
    """
    _ensure_model_loaded()
    if model is None:
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
        segments, info = model.transcribe(
            audio_float,
            beam_size=WHISPER_BEAM_SIZE,
            language=language,
            initial_prompt=initial_prompt,
            no_speech_threshold=WHISPER_NO_SPEECH_THRESHOLD,
            vad_filter=True,          # skip silent regions → fewer hallucinations
            vad_parameters={"min_silence_duration_ms": 300},
            condition_on_previous_text=False,
            temperature=0.0,
        )

        # segments is a generator — consume it
        text = "".join(seg.text for seg in segments).strip()

        if apply_corrections:
            text = _apply_text_corrections(text)

        logger.info(f"{log_prefix} Result (lang={info.language}, p={info.language_probability:.2f}): {text}")
        return text

    except FileNotFoundError as e:
        logger.error(f"{log_prefix} File not found: {audio_path} — {e}")
        return ""
    except Exception as e:
        import traceback
        logger.error(f"{log_prefix} Transcription error: {e}")
        logger.error(f"{log_prefix} {traceback.format_exc()}")
        return ""
