import sounddevice as sd
import scipy.io.wavfile as wav
import os
import uuid


# Directory to store recordings
AUDIO_DIR = os.path.join("backend", "data", "audio")


def record_audio(
    duration: int = 5,
    sample_rate: int = 16000
) -> str:
    """
    Records audio from default microphone and saves as WAV.
    Returns the path of the saved file.
    """

    try:
        # Ensure directory exists
        os.makedirs(AUDIO_DIR, exist_ok=True)

        # Unique filename to prevent overwrite
        filename = f"{uuid.uuid4()}.wav"
        filepath = os.path.join(AUDIO_DIR, filename)

        print("🎙 Recording...")

        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )

        sd.wait()

        wav.write(filepath, sample_rate, audio)

        print(f"✅ Audio saved at: {filepath}")

        return filepath

    except Exception as e:
        print(f"[Recorder Error] {e}")
        return ""
