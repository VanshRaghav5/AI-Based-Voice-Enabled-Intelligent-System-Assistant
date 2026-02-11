from fastapi import APIRouter
from backend.voice.recorder import record_audio
from backend.voice.stt import speech_to_text
from backend.voice.tts import speak
from backend.logic.intent import detect_intent, handle_intent

router = APIRouter()


@router.post("/voice/test")
def voice_test():
    record_audio(duration=5)

    text = speech_to_text()

    intent = detect_intent(text)
    response = handle_intent(intent, text)

    speak(response)

    return {
        "status": "success",
        "transcript": text,
        "intent": intent,
        "response": response,
        "mode": "offline"
    }