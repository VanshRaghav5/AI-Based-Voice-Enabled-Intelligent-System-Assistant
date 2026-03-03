"""Tests for Speech-to-Text (STT) module."""
import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestWhisperEngine:
    """Test cases for Whisper STT engine."""
    
    @patch('backend.voice_engine.stt.whisper_engine.whisper')
    def test_whisper_model_loads(self, mock_whisper):
        """Test that Whisper model can be loaded."""
        # Arrange
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        
        # Act
        from backend.voice_engine.stt.whisper_engine import load_whisper_model
        model = load_whisper_model()
        
        # Assert
        mock_whisper.load_model.assert_called_once()
        assert model is not None
    
    @patch('backend.voice_engine.stt.whisper_engine.whisper')
    def test_transcribe_audio_success(self, mock_whisper, sample_audio_path):
        """Test successful audio transcription."""
        # Arrange
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "hello world",
            "language": "en"
        }
        mock_whisper.load_model.return_value = mock_model
        
        # Act
        from backend.voice_engine.stt.whisper_engine import transcribe_audio
        result = transcribe_audio(sample_audio_path)
        
        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('backend.voice_engine.stt.whisper_engine.whisper')
    def test_transcribe_handles_empty_audio(self, mock_whisper):
        """Test transcription handles empty/invalid audio gracefully."""
        # Arrange
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "", "language": "en"}
        mock_whisper.load_model.return_value = mock_model
        
        # Act
        from backend.voice_engine.stt.whisper_engine import transcribe_audio
        result = transcribe_audio("fake_path.wav")
        
        # Assert
        assert result == ""
    
    @patch('backend.voice_engine.stt.whisper_engine.torch')
    @patch('backend.voice_engine.stt.whisper_engine.whisper')
    def test_gpu_detection(self, mock_whisper, mock_torch):
        """Test GPU availability detection."""
        # Arrange
        mock_torch.cuda.is_available.return_value = True
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        
        # Act
        from backend.voice_engine.stt.whisper_engine import load_whisper_model
        model = load_whisper_model()
        
        # Assert
        mock_torch.cuda.is_available.assert_called()
        assert model is not None


class TestSTTIntegration:
    """Integration tests for STT module."""
    
    @patch('backend.voice_engine.stt.whisper_engine.whisper')
    def test_multiple_transcriptions(self, mock_whisper, sample_audio_path):
        """Test multiple consecutive transcriptions."""
        # Arrange
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = [
            {"text": "first command", "language": "en"},
            {"text": "second command", "language": "en"},
        ]
        mock_whisper.load_model.return_value = mock_model
        
        # Act
        from backend.voice_engine.stt.whisper_engine import transcribe_audio
        result1 = transcribe_audio(sample_audio_path)
        result2 = transcribe_audio(sample_audio_path)
        
        # Assert
        assert "first" in result1.lower()
        assert "second" in result2.lower()
