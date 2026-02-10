from fastapi import APIRouter
from backend.voice.recorder import record_audio
from backend.voice.stt import speech_to_text
from backend.voice.tts import speak

router = APIRouter()


@router.post("/voice/test")
def voice_test():
    """
    Offline voice pipeline:
    Mic → Whisper → Piper
    """
    record_audio(duration=5)

    text = speech_to_text()
    response = f"You said: {text}"

    speak(response)

    return {
        "status": "success",
        "transcript": text,
        "response": response,
        "mode": "offline",
        "stt": "whisper",
        "tts": "piper"
    }
