import sounddevice as sd
import scipy.io.wavfile as wav


def record_audio(
    filename="input.wav",
    duration=5,
    sample_rate=16000
):
    """
    Records audio from default microphone and saves as WAV.
    """
    print("🎙 Recording...")
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16"
    )
    sd.wait()
    wav.write(filename, sample_rate, audio)
    print("✅ Audio saved:", filename)
