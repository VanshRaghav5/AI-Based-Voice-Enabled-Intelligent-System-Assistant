"""
Tests for the faster-whisper STT engine.

Covers:
  - Model loading (mocked)
  - transcribe_audio() â€” file-based path
  - transcribe_numpy() â€” in-memory zero-latency path
  - _to_float32_mono() â€” dtype normalisation + resampling
  - _apply_text_corrections() â€” regex substitutions
  - Edge cases: missing file, silent audio, too-short clip
  - Live smoke test with a synthetic 16-kHz sine-wave WAV
"""

import os
import tempfile
import numpy as np
import pytest
import scipy.io.wavfile as wavfile
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_RATE = 16000


def _make_sine_wav(path: str, freq: float = 440.0, duration: float = 1.5,
                   sample_rate: int = SAMPLE_RATE) -> str:
    """Write a mono 16-bit sine-wave WAV file and return its path."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio = (np.sin(2 * np.pi * freq * t) * 16000).astype(np.int16)
    wavfile.write(path, sample_rate, audio)
    return path


def _make_sine_array(freq: float = 440.0, duration: float = 1.5,
                     sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Return a mono int16 sine-wave array."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return (np.sin(2 * np.pi * freq * t) * 16000).astype(np.int16)


# ---------------------------------------------------------------------------
# _to_float32_mono â€” dtype + channel + resample normalisation
# ---------------------------------------------------------------------------

class TestToFloat32Mono:
    """Unit tests for the internal audio normalisation helper."""

    def setup_method(self):
        from backend.services.voice.stt.faster_whisper_engine import _to_float32_mono
        self._fn = _to_float32_mono

    def test_int16_normalisation(self):
        audio = np.array([0, 16384, -16384, 32767], dtype=np.int16)
        result, sr = self._fn(audio, SAMPLE_RATE)
        assert result.dtype == np.float32
        assert result.max() <= 1.0
        assert result.min() >= -1.0

    def test_int32_normalisation(self):
        audio = np.array([0, 1_073_741_824, -1_073_741_824], dtype=np.int32)
        result, sr = self._fn(audio, SAMPLE_RATE)
        assert result.dtype == np.float32
        assert abs(result[1] - 0.5) < 0.01

    def test_uint8_normalisation(self):
        audio = np.array([128, 255, 0], dtype=np.uint8)
        result, sr = self._fn(audio, SAMPLE_RATE)
        assert result.dtype == np.float32
        assert abs(result[0]) < 0.01   # 128 â†’ ~0.0

    def test_float32_passthrough(self):
        audio = np.array([0.0, 0.5, -0.5], dtype=np.float32)
        result, sr = self._fn(audio, SAMPLE_RATE)
        np.testing.assert_array_almost_equal(result, audio)

    def test_stereo_to_mono(self):
        """Stereo (N, 2) should be collapsed to (N,) mono."""
        stereo = np.ones((100, 2), dtype=np.int16) * 1000
        result, sr = self._fn(stereo, SAMPLE_RATE)
        assert result.ndim == 1
        assert len(result) == 100

    def test_resample_44100_to_16000(self):
        """44.1 kHz input must be resampled to 16 kHz."""
        orig_sr = 44100
        audio = np.zeros(int(orig_sr * 1.0), dtype=np.int16)
        result, sr = self._fn(audio, orig_sr)
        assert sr == SAMPLE_RATE
        # Expected output length â‰ˆ 16000 samples (Â±5%)
        assert abs(len(result) - SAMPLE_RATE) < SAMPLE_RATE * 0.05

    def test_already_16k_unchanged_sr(self):
        audio = np.zeros(SAMPLE_RATE, dtype=np.int16)
        result, sr = self._fn(audio, SAMPLE_RATE)
        assert sr == SAMPLE_RATE
        assert len(result) == SAMPLE_RATE


# ---------------------------------------------------------------------------
# _apply_text_corrections
# ---------------------------------------------------------------------------

class TestApplyTextCorrections:
    """Unit tests for the transcript correction helper."""

    def setup_method(self):
        from backend.services.voice.stt.faster_whisper_engine import _apply_text_corrections
        self._fn = _apply_text_corrections

    def test_empty_string_returns_empty(self):
        assert self._fn("") == ""

    def test_none_like_empty(self):
        # The function guards for falsy values
        assert self._fn("") == ""

    def test_whitespace_collapsed(self):
        result = self._fn("hello   world")
        assert result == "hello world"

    def test_correction_applied(self):
        """Configured correction 'swam' â†’ 'Swayam' should fire."""
        result = self._fn("I am swam here")
        assert "Swayam" in result

    def test_correction_case_insensitive(self):
        result = self._fn("SWAM is here")
        assert "Swayam" in result

    def test_correction_whole_word_only(self):
        """'swam' inside another word should NOT be replaced."""
        result = self._fn("blueswamberg")
        assert "Swayam" not in result


# ---------------------------------------------------------------------------
# _preprocess_for_noise
# ---------------------------------------------------------------------------

class TestPreprocessForNoise:
    """Unit tests for denoise + normalization preprocessing."""

    def setup_method(self):
        from backend.services.voice.stt.faster_whisper_engine import _preprocess_for_noise
        self._fn = _preprocess_for_noise

    def test_empty_audio_passthrough(self):
        empty = np.array([], dtype=np.float32)
        result = self._fn(empty)
        assert result.size == 0

    def test_normalizes_peak_and_removes_dc_bias(self, monkeypatch):
        from backend.services.voice.stt import faster_whisper_engine as eng
        monkeypatch.setattr(eng, "WHISPER_ENABLE_DENOISE", False, raising=False)
        monkeypatch.setattr(eng, "WHISPER_PREEMPHASIS_ALPHA", 0.0, raising=False)
        monkeypatch.setattr(eng, "WHISPER_NORMALIZE_TARGET_PEAK", 0.5, raising=False)

        biased = np.array([0.9, 1.0, 0.8, 0.7], dtype=np.float32)
        result = self._fn(biased)

        assert np.max(np.abs(result)) <= 0.5001
        assert abs(float(np.mean(result))) < 0.05

    def test_denoise_gate_suppresses_weak_noise(self, monkeypatch):
        from backend.services.voice.stt import faster_whisper_engine as eng
        monkeypatch.setattr(eng, "WHISPER_ENABLE_DENOISE", True, raising=False)
        monkeypatch.setattr(eng, "WHISPER_DENOISE_NOISE_PERCENTILE", 35.0, raising=False)
        monkeypatch.setattr(eng, "WHISPER_DENOISE_GATE_MULTIPLIER", 2.0, raising=False)
        monkeypatch.setattr(eng, "WHISPER_PREEMPHASIS_ALPHA", 0.0, raising=False)

        audio = np.array([0.001, -0.001, 0.002, -0.002, 0.2, -0.25], dtype=np.float32)
        result = self._fn(audio)

        # Several near-noise-floor samples should be gated to zero.
        assert int(np.count_nonzero(np.isclose(result, 0.0))) >= 2


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

class TestFasterWhisperModelLoad:

    @patch("backend.services.voice.stt.faster_whisper_engine.WhisperModel")
    def test_load_sets_global_model(self, mock_cls):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = None  # force reload
        result = eng.load_whisper_model()

        assert result is mock_instance
        assert eng.model is mock_instance

    @patch("backend.services.voice.stt.faster_whisper_engine.WhisperModel",
           side_effect=RuntimeError("CUDA OOM"))
    def test_load_failure_returns_none(self, mock_cls):
        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = None
        result = eng.load_whisper_model()
        assert result is None
        assert eng.model is None


# ---------------------------------------------------------------------------
# transcribe_audio() â€” file-based path
# ---------------------------------------------------------------------------

class TestTranscribeAudio:

    def _make_mock_model(self, transcript: str = "hello world"):
        """Return a mock WhisperModel that yields one segment."""
        seg = MagicMock()
        seg.text = " " + transcript

        info = MagicMock()
        info.language = "en"
        info.language_probability = 0.99

        mock_model = MagicMock()
        mock_model.transcribe.return_value = (iter([seg]), info)
        return mock_model

    def test_transcribes_valid_wav(self, tmp_path):
        wav_path = _make_sine_wav(str(tmp_path / "test.wav"))

        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = self._make_mock_model("set volume to 50")

        result = eng.transcribe_audio(wav_path)
        assert result == "set volume to 50"

    def test_missing_file_returns_empty(self):
        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = self._make_mock_model()

        result = eng.transcribe_audio("/nonexistent/path/audio.wav")
        assert result == ""

    def test_model_none_returns_empty(self, tmp_path):
        wav_path = _make_sine_wav(str(tmp_path / "test.wav"))

        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = None

        result = eng.transcribe_audio(wav_path)
        assert result == ""

    def test_corrections_applied(self, tmp_path):
        wav_path = _make_sine_wav(str(tmp_path / "test.wav"))

        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = self._make_mock_model("call swam please")

        result = eng.transcribe_audio(wav_path, apply_corrections=True)
        assert "Swayam" in result

    def test_corrections_skipped_when_disabled(self, tmp_path):
        wav_path = _make_sine_wav(str(tmp_path / "test.wav"))

        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = self._make_mock_model("call swam please")

        result = eng.transcribe_audio(wav_path, apply_corrections=False)
        assert "swam" in result.lower()

    def test_language_override(self, tmp_path):
        wav_path = _make_sine_wav(str(tmp_path / "test.wav"))
        captured = {}

        def fake_transcribe(audio, **kwargs):
            captured.update(kwargs)
            seg = MagicMock(); seg.text = "hello"
            info = MagicMock(); info.language = "fr"; info.language_probability = 0.9
            return iter([seg]), info

        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = MagicMock()
        eng.model.transcribe.side_effect = fake_transcribe

        eng.transcribe_audio(wav_path, language_override="fr")
        assert captured.get("language") == "fr"


# ---------------------------------------------------------------------------
# transcribe_numpy() â€” in-memory zero-latency path
# ---------------------------------------------------------------------------

class TestTranscribeNumpy:

    def _make_mock_model(self, transcript: str = "open youtube"):
        seg = MagicMock(); seg.text = " " + transcript
        info = MagicMock(); info.language = "en"; info.language_probability = 0.98
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (iter([seg]), info)
        return mock_model

    def test_transcribes_int16_array(self):
        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = self._make_mock_model("open youtube")

        audio = _make_sine_array()
        result = eng.transcribe_numpy(audio, SAMPLE_RATE)
        assert result == "open youtube"

    def test_model_none_returns_empty(self):
        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = None

        result = eng.transcribe_numpy(_make_sine_array(), SAMPLE_RATE)
        assert result == ""

    def test_too_short_clip_returns_empty(self):
        """Arrays shorter than 0.3 s should be silently rejected."""
        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = self._make_mock_model()

        short = np.zeros(int(SAMPLE_RATE * 0.1), dtype=np.int16)
        result = eng.transcribe_numpy(short, SAMPLE_RATE)
        assert result == ""

    def test_accepts_44100_input_resamples(self):
        """Passing 44.1 kHz array should resample and not crash."""
        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = self._make_mock_model("volume up")

        audio_44k = (np.sin(np.linspace(0, 2 * np.pi * 440, 44100)) * 16000).astype(np.int16)
        result = eng.transcribe_numpy(audio_44k, 44100)
        assert result == "volume up"

    def test_corrections_applied_numpy(self):
        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = self._make_mock_model("hey swam how are you")

        result = eng.transcribe_numpy(_make_sine_array(), SAMPLE_RATE)
        assert "Swayam" in result

    def test_transcription_exception_returns_empty(self):
        from backend.services.voice.stt import faster_whisper_engine as eng
        eng.model = MagicMock()
        eng.model.transcribe.side_effect = RuntimeError("GPU exploded")

        result = eng.transcribe_numpy(_make_sine_array(), SAMPLE_RATE)
        assert result == ""


# ---------------------------------------------------------------------------
# Live smoke test â€” uses the REAL loaded model (no mocks)
# Skipped automatically if model failed to load at import time.
# ---------------------------------------------------------------------------

class TestLiveFasterWhisper:
    """
    Smoke test: runs actual faster-whisper inference on a synthetic WAV.
    The sine wave won't produce real speech output; the test just confirms
    the pipeline doesn't crash and returns a string (including empty string).
    Mark with pytest.mark.slow if you want to exclude from CI.
    """

    @pytest.fixture(autouse=True)
    def _restore_model(self):
        """Restore whatever model state was before the test."""
        from backend.services.voice.stt import faster_whisper_engine as eng
        original = eng.model
        yield
        eng.model = original

    def test_live_transcribe_audio_does_not_crash(self, tmp_path):
        from backend.services.voice.stt import faster_whisper_engine as eng
        # Reload production model if it was replaced by a mock
        if eng.model is None or isinstance(eng.model, MagicMock):
            eng.load_whisper_model()

        if eng.model is None:
            pytest.skip("faster-whisper model not available")

        wav_path = _make_sine_wav(str(tmp_path / "live_smoke.wav"))
        result = eng.transcribe_audio(wav_path)
        assert isinstance(result, str)

    def test_live_transcribe_numpy_does_not_crash(self):
        from backend.services.voice.stt import faster_whisper_engine as eng
        if eng.model is None or isinstance(eng.model, MagicMock):
            eng.load_whisper_model()

        if eng.model is None:
            pytest.skip("faster-whisper model not available")

        audio = _make_sine_array()
        result = eng.transcribe_numpy(audio, SAMPLE_RATE)
        assert isinstance(result, str)

    def test_live_short_clip_rejected(self):
        from backend.services.voice.stt import faster_whisper_engine as eng
        if eng.model is None or isinstance(eng.model, MagicMock):
            eng.load_whisper_model()

        if eng.model is None:
            pytest.skip("faster-whisper model not available")

        short = np.zeros(100, dtype=np.int16)
        result = eng.transcribe_numpy(short, SAMPLE_RATE)
        assert result == ""
