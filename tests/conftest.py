"""Pytest configuration and shared fixtures."""
import pytest
import os
import sys
from unittest.mock import MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


@pytest.fixture
def mock_whisper_model():
    """Mock Whisper model for testing."""
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "text": "test command",
        "language": "en"
    }
    return mock_model


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry for testing."""
    from backend.core.tool_registry import ToolRegistry
    return ToolRegistry()


@pytest.fixture
def sample_audio_path(tmp_path):
    """Create a temporary audio file path."""
    audio_file = tmp_path / "test_audio.wav"
    audio_file.write_bytes(b"FAKE_AUDIO_DATA")
    return str(audio_file)


@pytest.fixture
def sample_execution_plan():
    """Sample execution plan for testing."""
    return {
        "steps": [
            {
                "tool": "file.create",
                "args": {"path": "test.txt"}
            }
        ]
    }


@pytest.fixture
def mock_logger():
    """Mock logger to prevent actual logging during tests."""
    return MagicMock()
