import whisper

# Load once (important for performance)
model = whisper.load_model("small")


def speech_to_text(audio_path="input.wav") -> str:
    """
    Converts speech audio to text using Whisper.
    """
    print("🧠 Transcribing...")
    result = model.transcribe(audio_path)
    return result["text"].strip()
