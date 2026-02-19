import whisper
import torch

from backend.config.logger import logger


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Whisper running on: {DEVICE}")

try:
    model = whisper.load_model("small", device=DEVICE)
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.error(f"[Whisper Load Error] {e}")
    model = None


def transcribe_audio(audio_path: str) -> str:

    if model is None:
        logger.error("[Whisper Error] Model not loaded.")
        return ""

    try:
        logger.info("Transcribing audio...")

        result = model.transcribe(
            audio_path,
            fp16=(DEVICE == "cuda"),
            temperature=0.0,
            condition_on_previous_text=False
        )

        text = result.get("text", "").strip()
        logger.info(f"Transcription result: {text}")

        return text

    except Exception as e:
        logger.error(f"[Whisper Transcription Error] {e}")
        return ""
