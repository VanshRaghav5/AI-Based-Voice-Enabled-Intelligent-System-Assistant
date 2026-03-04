import whisper
import torch
import os
import re
import numpy as np
import scipy.io.wavfile as wavfile

from backend.config.logger import logger
from backend.config.settings import (
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


def load_whisper_model():
    """Load and cache Whisper model using configured settings."""
    global model

    try:
        model = whisper.load_model(WHISPER_MODEL, device=DEVICE)
        logger.info(f"Whisper '{WHISPER_MODEL}' model loaded successfully")
    except Exception as e:
        logger.error(f"[Whisper Load Error] {e}")
        model = None

    return model


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


load_whisper_model()


def transcribe_audio(audio_path: str) -> str:

    if model is None:
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
        logger.info(f"[Whisper] Transcribing: {audio_path} (size: {file_size} bytes)")

        # Load audio via scipy to bypass FFmpeg dependency on Windows
        sample_rate, audio_data = wavfile.read(audio_path)
        
        # Convert int16 PCM to float32 normalized [-1.0, 1.0]
        audio_float = audio_data.astype(np.float32) / 32768.0
        
        # Whisper expects mono; squeeze if needed
        if audio_float.ndim == 2:
            audio_float = audio_float.mean(axis=1)

        # Normalize loudness for clearer decoding across different mic levels
        audio_float = _normalize_audio(audio_float)

        # Balanced transcription parameters for clarity + responsiveness
        result = model.transcribe(
            audio_float,
            fp16=(DEVICE == "cuda"),
            temperature=0.0,
            condition_on_previous_text=False,
            no_speech_threshold=WHISPER_NO_SPEECH_THRESHOLD,
            language=WHISPER_LANGUAGE,
            beam_size=WHISPER_BEAM_SIZE,
            best_of=WHISPER_BEST_OF,
            initial_prompt=WHISPER_INITIAL_PROMPT,
        )

        text = result.get("text", "").strip()
        text = _apply_text_corrections(text)
        logger.info(f"[Whisper] Transcription result: {text}")

        return text

    except FileNotFoundError as e:
        logger.error(f"[Whisper Error] File not found: {audio_path} - {e}")
        return ""
    except Exception as e:
        import traceback
        logger.error(f"[Whisper Transcription Error] {e}")
        logger.error(f"[Whisper Traceback] {traceback.format_exc()}")
        return ""
