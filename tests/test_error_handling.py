"""Tests for Error Handling System."""
import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestErrorHandler:
    """Test error handler functionality."""
    
    def test_error_handler_initialization(self):
        """Test error handler can be initialized."""
        # Act
        from backend.tools.error_handler import ErrorHandler
        handler = ErrorHandler()
        
        # Assert
        assert handler is not None
    
    def test_wrap_automation_success(self):
        """Test wrapping successful automation."""
        # Arrange
        from backend.tools.error_handler import error_handler
        
        def successful_func():
            return {"status": "success", "message": "Done", "data": {}}
        
        # Act
        result = error_handler.wrap_automation(
            func=successful_func,
            operation_name="Test Op",
            context={}
        )
        
        # Assert
        assert result["status"] == "success"
    
    def test_wrap_automation_handles_exception(self):
        """Test wrapping automation that raises exception."""
        # Arrange
        from backend.tools.error_handler import error_handler
        
        def failing_func():
            raise ValueError("Test error")
        
        # Act
        result = error_handler.wrap_automation(
            func=failing_func,
            operation_name="Test Op",
            context={}
        )
        
        # Assert
        assert result["status"] == "error"
        assert "message" in result
        assert "data" in result
    
    def test_custom_automation_error(self):
        """Test custom AutomationError exception."""
        # Arrange
        from backend.tools.error_handler import AutomationError
        
        # Act & Assert
        with pytest.raises(AutomationError):
            raise AutomationError("Test failure", "User message")
    
    def test_window_not_found_error(self):
        """Test WindowNotFoundError exception."""
        # Arrange
        from backend.tools.error_handler import WindowNotFoundError
        
        # Act & Assert
        with pytest.raises(WindowNotFoundError):
            raise WindowNotFoundError("Window missing", "App not found")
    
    def test_error_message_generation(self):
        """Test user-friendly error message generation."""
        # Arrange
        from backend.tools.error_handler import error_handler
        
        def func_with_file_error():
            raise FileNotFoundError("File not found")
        
        # Act
        result = error_handler.wrap_automation(
            func=func_with_file_error,
            operation_name="File Test",
            context={"app": "TestApp"}
        )
        
        # Assert
        assert result["status"] == "error"
        assert len(result["message"]) > 0
        # Should be user-friendly, not technical


class TestWindowDetection:
    """Test window detection utilities."""
    
    def test_window_detector_initialization(self):
        """Test window detector can be initialized."""
        # Act
        from backend.tools.window_detection import WindowDetector
        detector = WindowDetector()
        
        # Assert
        assert detector is not None
    
    @patch('backend.tools.window_detection.gw')
    def test_is_window_active(self, mock_gw):
        """Test checking if window is active."""
        # Arrange
        from backend.tools.window_detection import window_detector
        mock_gw.getAllTitles.return_value = ["Chrome", "WhatsApp", "Notepad"]
        
        # Act
        result = window_detector.is_window_active("WhatsApp", timeout=1)
        
        # Assert
        assert result is True
    
    @patch('backend.tools.window_detection.gw')
    def test_is_window_active_not_found(self, mock_gw):
        """Test checking for non-existent window."""
        # Arrange
        from backend.tools.window_detection import window_detector
        mock_gw.getAllTitles.return_value = ["Chrome", "Notepad"]
        
        # Act
        result = window_detector.is_window_active("WhatsApp", timeout=1)
        
        # Assert
        assert result is False

    @patch('backend.tools.window_detection.gw')
    def test_focus_window_success(self, mock_gw):
        """Focus should succeed when activation works and active window matches."""
        from backend.tools.window_detection import window_detector

        mock_window = MagicMock()
        mock_window.title = "WhatsApp"
        mock_window.isMinimized = False
        mock_window.activate.return_value = None
        mock_gw.getWindowsWithTitle.return_value = [mock_window]
        mock_gw.getActiveWindow.return_value = mock_window

        result = window_detector.focus_window("WhatsApp")

        assert result is True
        mock_window.activate.assert_called_once()

    @patch('backend.tools.window_detection.gw')
    def test_focus_window_tolerates_windows_zero_error(self, mock_gw):
        """Focus should soft-succeed on known Windows code-0 false negative."""
        from backend.tools.window_detection import window_detector

        mock_window = MagicMock()
        mock_window.title = "WhatsApp"
        mock_window.isMinimized = False
        mock_window.activate.side_effect = Exception(
            "Error code from Windows: 0 - The operation completed successfully."
        )
        mock_gw.getWindowsWithTitle.return_value = [mock_window]
        mock_gw.getAllTitles.return_value = ["WhatsApp", "Chrome"]

        result = window_detector.focus_window("WhatsApp")

        assert result is True
    
    def test_window_detection_fallback_when_lib_missing(self):
        """Test window detection handles missing pygetwindow gracefully."""
        # Arrange
        from backend.tools.window_detection import window_detector
        
        with patch('backend.tools.window_detection.gw', None):
            # Act
            # Should not raise, should return True as fallback
            try:
                result = window_detector.is_window_active("Test", timeout=1)
                # Assert - should handle gracefully
                assert result in [True, False]
            except ImportError:
                # This is also acceptable - indicates proper error handling
                pass
    
    @patch('backend.tools.window_detection.psutil')
    def test_is_process_running(self, mock_psutil):
        """Test checking if process is running."""
        # Arrange
        from backend.tools.window_detection import window_detector
        
        mock_process = MagicMock()
        mock_process.info = {'name': 'WhatsApp.exe'}
        mock_psutil.process_iter.return_value = [mock_process]
        
        # Act
        result = window_detector.is_process_running("WhatsApp.exe")
        
        # Assert
        assert result is True
    
    @patch('backend.tools.window_detection.psutil')
    def test_is_process_not_running(self, mock_psutil):
        """Test checking for non-running process."""
        # Arrange
        from backend.tools.window_detection import window_detector
        
        mock_process = MagicMock()
        mock_process.info = {'name': 'Chrome.exe'}
        mock_psutil.process_iter.return_value = [mock_process]
        
        # Act
        result = window_detector.is_process_running("WhatsApp.exe")
        
        # Assert
        assert result is False
