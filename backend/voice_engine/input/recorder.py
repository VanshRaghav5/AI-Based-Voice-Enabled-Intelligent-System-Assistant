import sounddevice as sd
import scipy.io.wavfile as wav
import os
import uuid


AUDIO_DIR = os.path.join("backend", "data", "audio")


def record_audio(duration=4, sample_rate=16000) -> str:
    """
    Simple fixed-duration recording.
    """

    os.makedirs(AUDIO_DIR, exist_ok=True)

    filename = f"{uuid.uuid4()}.wav"
    filepath = os.path.join(AUDIO_DIR, filename)

    print("🎙 Recording... Speak now.")

    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    wav.write(filepath, sample_rate, audio)

    print("✅ Recording complete")

    return filepath
