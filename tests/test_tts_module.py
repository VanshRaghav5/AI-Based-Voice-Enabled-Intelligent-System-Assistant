"""Tests for Text-to-Speech (TTS) module."""

import os
import sys
from unittest.mock import MagicMock, patch


# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestPiperTTS:
    """Test cases for Piper TTS engine."""

    @patch('backend.voice_engine.tts.tts_engine.os.remove')
    @patch('backend.voice_engine.tts.tts_engine.sd.wait')
    @patch('backend.voice_engine.tts.tts_engine.sd.play')
    @patch('backend.voice_engine.tts.tts_engine.wav.read')
    @patch('backend.voice_engine.tts.tts_engine.subprocess.run')
    @patch('backend.voice_engine.tts.tts_engine.os.path.exists')
    def test_speak_text_success(
        self,
        mock_exists,
        mock_run,
        mock_wav_read,
        mock_sd_play,
        mock_sd_wait,
        mock_remove,
    ):
        """TTS should run Piper, play the WAV, and return success."""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        mock_wav_read.return_value = (22050, MagicMock())

        from backend.voice_engine.tts.tts_engine import speak_text

        result = speak_text("Hello world")

        assert result == "success"
        mock_run.assert_called_once()
        mock_sd_play.assert_called_once()
        mock_sd_wait.assert_called_once()
        assert mock_remove.called

    @patch('backend.voice_engine.tts.tts_engine.subprocess.run')
    def test_speak_skips_empty_text(self, mock_run):
        """Empty text should be ignored without invoking Piper."""
        from backend.voice_engine.tts.tts_engine import speak_text

        result = speak_text("")

        assert result == ""
        mock_run.assert_not_called()

    @patch('backend.voice_engine.tts.tts_engine.os.path.exists', return_value=False)
    def test_speak_handles_missing_piper(self, mock_exists):
        """If Piper executable is missing, function should fail safely."""
        from backend.voice_engine.tts.tts_engine import speak_text

        result = speak_text("hello")
        assert result == ""


class TestVoiceCatalog:
    """Tests for voice/accent discovery and model resolution."""

    @patch('backend.voice_engine.tts.tts_engine.os.listdir', return_value=['en_US-danny-low.onnx', 'en_GB-jenny-medium.onnx'])
    @patch('backend.voice_engine.tts.tts_engine.os.path.isfile', return_value=True)
    @patch('backend.voice_engine.tts.tts_engine.os.path.exists', return_value=True)
    def test_get_available_voices_includes_discovered_models(self, mock_exists, mock_isfile, mock_listdir):
        from backend.voice_engine.tts.tts_engine import get_available_voices

        voices = get_available_voices()
        assert 'en_US' in voices
        assert 'danny' in voices['en_US']
        assert 'en_GB' in voices
        assert 'jenny' in voices['en_GB']

    @patch('backend.voice_engine.tts.tts_engine.os.path.exists', return_value=True)
    @patch('backend.voice_engine.tts.tts_engine.os.listdir', return_value=['en_US-danny-low.onnx'])
    @patch('backend.voice_engine.tts.tts_engine.os.path.isfile', return_value=True)
    def test_resolve_voice_model_falls_back_when_voice_missing(self, mock_isfile, mock_listdir, mock_exists):
        from backend.voice_engine.tts.tts_engine import _resolve_voice_model

        model_path, config_path, voice, accent = _resolve_voice_model(voice='missing_voice', accent='en_AU')

        assert model_path.endswith('en_US-danny-low.onnx')
        assert config_path.endswith('en_US-danny-low.onnx.json')
        assert voice == 'danny'
        assert accent == 'en_US'
