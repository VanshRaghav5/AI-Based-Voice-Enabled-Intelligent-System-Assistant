import whisper
import torch


# ---------- DEVICE DETECTION ----------
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥 Whisper running on: {DEVICE}")

# ---------- LOAD MODEL ONCE ----------
try:
    model = whisper.load_model("small", device=DEVICE)
    print("✅ Whisper model loaded successfully")
except Exception as e:
    print(f"[Whisper Load Error] {e}")
    model = None


def transcribe_audio(audio_path: str) -> str:
    """
    Converts speech audio to text using Whisper.
    Returns transcribed text.
    """

    if model is None:
        print("[Whisper Error] Model not loaded.")
        return ""

    try:
        print("🧠 Transcribing...")

        result = model.transcribe(
                    audio_path,
                fp16=(DEVICE == "cuda")
            )



        return result["text"].strip()

    except Exception as e:
        print(f"[Whisper Transcription Error] {e}")
        return ""
