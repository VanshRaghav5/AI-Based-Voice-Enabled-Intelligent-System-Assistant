from voice_engine.input.recorder import record_audio
from voice_engine.stt.whisper_engine import transcribe_audio
from voice_engine.tts.tts_engine import speak_text


def listen() -> str:
    """
    Records audio from microphone
    Converts speech to text
    Returns transcribed text
    """
    try:
        audio_path = record_audio()
        text = transcribe_audio(audio_path)
        return text
    except Exception as e:
        print(f"[Voice Pipeline Error - Listen] {e}")
        return ""


def speak(text: str):
    """
    Converts text to speech
    Plays output audio
    """
    try:
        speak_text(text)
    except Exception as e:
        print(f"[Voice Pipeline Error - Speak] {e}")
