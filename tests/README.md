# Test Suite Documentation

## Overview
Comprehensive test suite for the AI-Based Voice Intelligent System Assistant.

## Test Structure

```
tests/
├── __init__.py                 # Test package init
├── conftest.py                 # Pytest configuration & shared fixtures
├── test_stt_module.py         # Speech-to-Text tests
├── test_tts_module.py         # Text-to-Speech tests
├── test_intent_parser.py      # Intent parsing & LLM tests
├── test_file_operations.py    # File operation tests (mocked)
├── test_automation_router.py  # Tool registry & executor tests
├── test_error_handling.py     # Error handling system tests
└── README.md                  # This file
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_stt_module.py
pytest tests/test_file_operations.py
```

### Run Specific Test Class
```bash
pytest tests/test_stt_module.py::TestWhisperEngine
```

### Run Specific Test Function
```bash
pytest tests/test_file_operations.py::TestFileDeleteTool::test_file_delete_success
```

### Run with Coverage Report
```bash
pytest --cov=backend --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Only Fast Tests (Skip Slow)
```bash
pytest -m "not slow"
```

## Test Categories

### Unit Tests
- **STT Module** (`test_stt_module.py`)
  - Whisper model loading
  - Audio transcription
  - GPU detection
  - Error handling

- **TTS Module** (`test_tts_module.py`)
  - Piper TTS initialization
  - Text-to-speech conversion
  - Audio cleanup
  - Configuration validation

- **Intent Parser** (`test_intent_parser.py`)
  - LLM client initialization
  - Ollama integration
  - Fallback keyword matching
  - Command parsing for file, WhatsApp, system operations

- **File Operations** (`test_file_operations.py`)
  - File create/delete/move (all mocked - no real file operations)
  - Folder create/delete (mocked)
  - Path validation
  - Error handling

- **Automation Router** (`test_automation_router.py`)
  - Tool registry operations
  - Tool registration and lookup
  - Executor functionality
  - Multi-step execution
  - Confirmation handling

- **Error Handling** (`test_error_handling.py`)
  - Error handler wrapper
  - Custom exceptions
  - Window detection
  - Process monitoring
  - User-friendly error messages

## Key Testing Features

### Mocking
All tests use extensive mocking to:
- **No Real File Operations**: Files are never actually created/deleted
- **No Real Process Launches**: Applications are not actually opened
- **No Real Network Calls**: SMTP, browsers not actually invoked
- **Isolated Testing**: Each test is completely independent

### Fixtures (conftest.py)
Shared test fixtures include:
- `mock_whisper_model`: Mock Whisper STT model
- `mock_tool_registry`: Mock tool registry
- `sample_audio_path`: Temporary test audio file
- `sample_execution_plan`: Sample LLM execution plan
- `mock_logger`: Mock logger to prevent actual logging

### Coverage
Tests aim for high code coverage:
- Core modules: 80%+ coverage target
- Critical paths: 100% coverage
- Error paths: Comprehensive coverage

## Test Best Practices

### 1. Arrange-Act-Assert Pattern
```python
def test_example(self):
    # Arrange - Set up test data and mocks
    mock_obj = MagicMock()
    
    # Act - Execute the code under test
    result = function_to_test(mock_obj)
    
    # Assert - Verify results
    assert result == expected_value
```

### 2. Use Descriptive Test Names
```python
def test_file_delete_success(self):  # ✅ Clear what's being tested
def test1(self):  # ❌ Unclear
```

### 3. Test One Thing Per Test
Each test should verify one specific behavior.

### 4. Mock External Dependencies
```python
@patch('module.external_dependency')
def test_with_mock(self, mock_dependency):
    mock_dependency.return_value = test_value
```

### 5. Use Fixtures for Common Setup
```python
@pytest.fixture
def common_setup():
    return setup_data()

def test_using_fixture(common_setup):
    assert common_setup is not None
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

### GitHub Actions Example
```yaml
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=backend --cov-report=xml
```

### Test Quality Metrics
- **Total Tests**: 40+ test cases
- **Coverage**: 70%+ (target: 80%)
- **Execution Time**: ~10-30 seconds (all tests)
- **Mocking**: 100% (no real file/system operations)

## Adding New Tests

### Template for New Test File
```python
"""Tests for [Module Name]."""
import pytest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestMyModule:
    """Test cases for MyModule."""
    
    def test_functionality(self):
        """Test specific functionality."""
        # Arrange
        # Act
        # Assert
        assert True
```

### Adding a New Test
1. Create test file: `test_new_module.py`
2. Import required modules
3. Create test classes
4. Write test functions with `test_` prefix
5. Use mocks for external dependencies
6. Run: `pytest tests/test_new_module.py`

## Troubleshooting

### Import Errors
If tests can't import backend modules:
```bash
# Make sure you're in project root
cd AI-Based-Voice-Enabled-Intelligent-System-Assistant

# Run tests from project root
pytest tests/
```

### Mock Not Working
Ensure patch path matches actual import:
```python
# If module does: from backend.x import y
@patch('backend.x.y')  # ✅ Correct

# Not:
@patch('x.y')  # ❌ Wrong
```

### Tests Hanging
Some tests may timeout if mocking is incomplete. Check:
- All external calls are mocked
- No actual file I/O
- No real process launches

## Test Maintenance

### Regular Updates
- Update tests when adding new features
- Keep mocks in sync with actual APIs
- Maintain >80% code coverage
- Review and update fixtures

### Refactoring Tests
- Extract common mocks to conftest.py
- Use parametrize for similar tests
- Keep tests DRY (Don't Repeat Yourself)

---

## Quick Commands Reference

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=backend

# Run specific file
pytest tests/test_stt_module.py

# Run verbose
pytest -v

# Generate HTML coverage report
pytest --cov=backend --cov-report=html
```

---

**Status**: 40+ comprehensive tests | 70%+ coverage | 100% mocked
