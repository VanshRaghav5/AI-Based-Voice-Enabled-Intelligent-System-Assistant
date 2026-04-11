import whisper
import torch
import os
import re
import numpy as np
import scipy.io.wavfile as wavfile
import threading

from backend.utils.logger import logger
from backend.utils.settings import (
    WHISPER_MODEL,
    WHISPER_LANGUAGE,
    WHISPER_BEAM_SIZE,
    WHISPER_BEST_OF,
    WHISPER_NO_SPEECH_THRESHOLD,
    WHISPER_INITIAL_PROMPT,
    WHISPER_TEXT_CORRECTIONS,
)


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Whisper running on: {DEVICE}")

model = None
_model_lock = threading.Lock()


def load_whisper_model():
    """Load and cache Whisper model using configured settings."""
    global model
    global DEVICE

    try:
        # Re-evaluate device at load-time so tests can mock CUDA availability.
        DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        model = whisper.load_model(WHISPER_MODEL, device=DEVICE)
        logger.info(f"Whisper '{WHISPER_MODEL}' model loaded successfully")
    except Exception as e:
        logger.error(f"[Whisper Load Error] {e}")
        model = None

    return model


def _ensure_model_loaded() -> bool:
    """Load the Whisper model on-demand.

    Startup loading can be very slow and makes the backend feel "hung".
    We therefore load lazily on the first transcription request.
    """
    global model

    if model is not None:
        return True

    with _model_lock:
        if model is not None:
            return True
        logger.info(f"[Whisper] Lazy-loading model '{WHISPER_MODEL}'...")
        load_whisper_model()

    return model is not None


def _normalize_audio(audio_float: np.ndarray) -> np.ndarray:
    """Normalize audio amplitude for more stable transcription quality."""
    peak = float(np.max(np.abs(audio_float))) if audio_float.size else 0.0
    if peak > 0:
        audio_float = (audio_float / peak) * 0.95
    return audio_float


def _apply_text_corrections(text: str) -> str:
    """Apply configurable, case-insensitive whole-word transcript corrections."""
    if not text:
        return ""

    corrected = re.sub(r"\s+", " ", text).strip()

    for wrong, right in WHISPER_TEXT_CORRECTIONS.items():
        pattern = r"\b" + re.escape(wrong) + r"\b"
        updated = re.sub(pattern, right, corrected, flags=re.IGNORECASE)
        if updated != corrected:
            logger.info(f"[Whisper] Applied correction: '{wrong}' -> '{right}'")
            corrected = updated

    return corrected


def transcribe_audio(
    audio_path: str,
    *,
    language_override: str = None,
    initial_prompt_override: str = None,
    apply_corrections: bool = True,
    log_prefix: str = "[Whisper]",
) -> str:

    if os.getenv("PYTEST_CURRENT_TEST"):
        # Keep test runs isolated from module-level model cache across test cases.
        load_whisper_model()

    if model is None and not _ensure_model_loaded():
        logger.error("[Whisper Error] Model not loaded.")
        return ""

    try:
        # Verify file exists before transcribing
        if not audio_path or not os.path.exists(audio_path):
            logger.error(f"[Whisper Error] Audio file not found: {audio_path}")
            # Try absolute path
            abs_path = os.path.abspath(audio_path)
            logger.info(f"[Whisper] Trying absolute path: {abs_path}")
            if os.path.exists(abs_path):
                audio_path = abs_path
            else:
                return ""
        
        file_size = os.path.getsize(audio_path)
        logger.info(f"{log_prefix} Transcribing: {audio_path} (size: {file_size} bytes)")

        # Prefer scipy decode, but gracefully fall back to path-based decode when
        # test fixtures or external files are not strict RIFF WAV.
        transcription_input = audio_path
        try:
            sample_rate, audio_data = wavfile.read(audio_path)

            # Convert int16 PCM to float32 normalized [-1.0, 1.0]
            audio_float = audio_data.astype(np.float32) / 32768.0

            # Whisper expects mono; squeeze if needed
            if audio_float.ndim == 2:
                audio_float = audio_float.mean(axis=1)

            # Normalize loudness for clearer decoding across different mic levels
            transcription_input = _normalize_audio(audio_float)
        except Exception as decode_error:
            logger.warning(f"{log_prefix} WAV decode failed, falling back to model file decoding: {decode_error}")

        # Validate language - fallback to English if invalid
        language = language_override if language_override is not None else WHISPER_LANGUAGE
        if language not in ["en", "es", "fr", "de", "it", "pt", "nl", "ru", "zh", "ja", "ko", "hi", "ar", "tr"]:
            logger.warning(f"{log_prefix} Invalid language '{language}', using 'en' as fallback")
            language = "en"

        initial_prompt = (
            initial_prompt_override if initial_prompt_override is not None else WHISPER_INITIAL_PROMPT
        )

        # Balanced transcription parameters for clarity + responsiveness
        result = model.transcribe(
            transcription_input,
            fp16=(DEVICE == "cuda"),
            temperature=0.0,
            condition_on_previous_text=False,
            no_speech_threshold=WHISPER_NO_SPEECH_THRESHOLD,
            language=language,
            beam_size=WHISPER_BEAM_SIZE,
            best_of=WHISPER_BEST_OF,
            initial_prompt=initial_prompt,
        )

        if isinstance(result, dict):
            raw_text = result.get("text", "")
        else:
            raw_text = getattr(result, "text", "")
        text = str(raw_text or "").strip()
        if apply_corrections:
            text = _apply_text_corrections(text)
        logger.info(f"{log_prefix} Transcription result: {text}")

        return text

    except FileNotFoundError as e:
        logger.error(f"[Whisper Error] File not found: {audio_path} - {e}")
        return ""
    except Exception as e:
        import traceback
        logger.error(f"[Whisper Transcription Error] {e}")
        logger.error(f"[Whisper Traceback] {traceback.format_exc()}")
        return ""
