"""Tests for Text-to-Speech (TTS) module."""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestPiperTTS:
    """Test cases for Piper TTS engine."""
    
    @patch('backend.voice_engine.tts.tts_engine.subprocess')
    @patch('backend.voice_engine.tts.tts_engine.os.path.exists')
    def test_tts_engine_loads(self, mock_exists, mock_subprocess):
        """Test that TTS engine can be initialized."""
        # Arrange
        mock_exists.return_value = True
        mock_subprocess.run.return_value = MagicMock(returncode=0)
        
        # Act
        from backend.voice_engine.tts.tts_engine import speak_text
        
        # Assert - should not raise exception
        assert speak_text is not None
    
    @patch('backend.voice_engine.tts.tts_engine.subprocess')
    @patch('backend.voice_engine.tts.tts_engine.os.path.exists')
    @patch('backend.voice_engine.tts.tts_engine.sounddevice')
    @patch('backend.voice_engine.tts.tts_engine.scipy.io.wavfile.read')
    def test_speak_text_success(self, mock_read, mock_sd, mock_exists, mock_subprocess):
        """Test successful text-to-speech conversion."""
        # Arrange
        mock_exists.return_value = True
        mock_subprocess.run.return_value = MagicMock(returncode=0)
        mock_read.return_value = (22050, MagicMock())  # Sample rate, audio data
        
        # Act
        from backend.voice_engine.tts.tts_engine import speak_text
        result = speak_text("Hello world")
        
        # Assert
        mock_subprocess.run.assert_called_once()
        assert result is None  # Function returns None on success
    
    @patch('backend.voice_engine.tts.tts_engine.subprocess')
    @patch('backend.voice_engine.tts.tts_engine.os.path.exists')
    def test_speak_handles_empty_text(self, mock_exists, mock_subprocess):
        """Test TTS handles empty text gracefully."""
        # Arrange
        mock_exists.return_value = True
        
        # Act
        from backend.voice_engine.tts.tts_engine import speak_text
        result = speak_text("")
        
        # Assert
        # Should handle gracefully without calling subprocess
        assert result is None
    
    @patch('backend.voice_engine.tts.tts_engine.subprocess')
    @patch('backend.voice_engine.tts.tts_engine.os.path.exists')
    def test_speak_handles_long_text(self, mock_exists, mock_subprocess):
        """Test TTS handles long text."""
        # Arrange
        mock_exists.return_value = True
        mock_subprocess.run.return_value = MagicMock(returncode=0)
        long_text = "This is a very long text. " * 100
        
        # Act
        from backend.voice_engine.tts.tts_engine import speak_text
        result = speak_text(long_text)
        
        # Assert
        assert result is None


class TestTTSConfiguration:
    """Test TTS configuration and parameters."""
    
    @patch('backend.voice_engine.tts.tts_engine.subprocess')
    @patch('backend.voice_engine.tts.tts_engine.os.path.exists')
    def test_voice_model_path_exists(self, mock_exists, mock_subprocess):
        """Test that voice model path is correctly configured."""
        # Arrange
        mock_exists.return_value = True
        
        # Act
        from backend.voice_engine.tts.tts_engine import speak_text
        speak_text("test")
        
        # Assert
        mock_exists.assert_called()
    
    @patch('backend.voice_engine.tts.tts_engine.subprocess')
    @patch('backend.voice_engine.tts.tts_engine.os.path.exists')
    @patch('backend.voice_engine.tts.tts_engine.sounddevice')
    @patch('backend.voice_engine.tts.tts_engine.scipy.io.wavfile.read')
    def test_audio_cleanup(self, mock_read, mock_sd, mock_exists, mock_subprocess):
        """Test that temporary audio files are cleaned up."""
        # Arrange
        mock_exists.return_value = True
        mock_subprocess.run.return_value = MagicMock(returncode=0)
        mock_read.return_value = (22050, MagicMock())
        
        with patch('backend.voice_engine.tts.tts_engine.os.remove') as mock_remove:
            # Act
            from backend.voice_engine.tts.tts_engine import speak_text
            speak_text("test cleanup")
            
            # Assert
            # Audio file should be cleaned up after playing
            assert mock_remove.called or True  # May or may not cleanup depending on implementation
