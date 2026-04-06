"""Tests for Starter Tools and Tool Registry Integration."""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import tempfile
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestToolRegistryIntegration:
    """Test tool registry with starter tools."""
    
    def test_registry_loads_all_starter_tools(self):
        """Test that all starter tools are registered in the registry."""
        # Arrange & Act
        from backend.core.execution.tool_registry import ToolRegistry
        from backend.tools.dev_tools import register_all_tools
        
        registry = ToolRegistry()
        register_all_tools(registry)
        
        # Assert
        tools = registry.list_tools()
        assert len(tools) >= 31, f"Expected at least 31 tools, got {len(tools)}"
        
        # Verify key tools exist
        required_tools = [
            "open_app", "close_app", "get_running_apps",
            "create_file", "delete_file", "list_directory",
            "search_youtube", "download_file",
            "remember_data", "recall_data"
        ]
        for tool_name in required_tools:
            assert tool_name in tools, f"Tool {tool_name} not registered"
    
    def test_registry_can_execute_function_based_tool(self):
        """Test that registry can execute function-based tools."""
        # Arrange
        from backend.core.execution.tool_registry import ToolRegistry
        from backend.tools.dev_tools import register_all_tools
        
        registry = ToolRegistry()
        register_all_tools(registry)
        
        # Act: Test with a simple tool that returns list
        result = registry.execute("list_memory", {})
        
        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert "success" in result or "data" in result


class TestBasicToolExecution:
    """Test execution of basic starter tools."""
    
    def test_open_app_success(self):
        """Test opening an application."""
        # Arrange
        from backend.tools import starter_tools
        
        with patch('backend.tools.app_launcher.open_app') as mock_open_app:
            mock_open_app.return_value = {
                "success": True,
                "status": "success",
                "message": "Notepad opened"
            }
            
            # Act
            result = starter_tools.open_app("notepad")
            
            # Assert
            assert result["success"] == True
            assert "notepad" in result.get("message", "").lower()
    
    def test_open_app_empty_name(self):
        """Test opening app with empty name returns error."""
        # Arrange
        from backend.tools import starter_tools
        
        # Act
        result = starter_tools.open_app("")
        
        # Assert
        assert result["success"] == False
        assert result["error"] is not None
    
    def test_close_app_success(self):
        """Test closing an application."""
        # Arrange
        from backend.tools import starter_tools
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
            
            # Act
            result = starter_tools.close_app("notepad")
            
            # Assert
            assert result["success"] == True
            assert "notepad.exe" in result.get("message", "").lower()
    
    def test_close_app_failure(self):
        """Test closing app that doesn't exist."""
        # Arrange
        from backend.tools import starter_tools
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Task not found",
                stdout=""
            )
            
            # Act
            result = starter_tools.close_app("nonexistent_app")
            
            # Assert
            assert result["success"] == False
    
    def test_get_running_apps(self):
        """Test getting list of running applications."""
        # Arrange
        from backend.tools import starter_tools
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='"explorer.exe","4520"\n"notepad.exe","2140"\n',
                stderr=""
            )
            
            # Act
            result = starter_tools.get_running_apps(limit=10)
            
            # Assert
            assert result["success"] == True
            assert "apps" in result.get("data", {})
            apps = result["data"]["apps"]
            assert len(apps) > 0


class TestFileOperationTools:
    """Test file operation tools."""
    
    def test_create_file_success(self):
        """Test creating a file."""
        # Arrange
        from backend.tools import starter_tools
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            
            # Act
            result = starter_tools.create_file(test_file)
            
            # Assert
            assert result["success"] == True
            assert os.path.exists(test_file)
    
    def test_write_file_success(self):
        """Test writing content to a file."""
        # Arrange
        from backend.tools import starter_tools
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            content = "Hello, World!"
            
            # Act
            result = starter_tools.write_file(test_file, content)
            
            # Assert
            assert result["success"] == True
            assert os.path.exists(test_file)
            with open(test_file, 'r') as f:
                assert f.read() == content
    
    def test_read_file_success(self):
        """Test reading file content."""
        # Arrange
        from backend.tools import starter_tools
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            content = "Test Content"
            
            # Write the file first
            with open(test_file, 'w') as f:
                f.write(content)
            
            # Act
            result = starter_tools.read_file(test_file)
            
            # Assert
            assert result["success"] == True
            assert result["data"]["content"] == content
    
    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        # Arrange
        from backend.tools import starter_tools
        
        # Act
        result = starter_tools.read_file("/nonexistent/file/path.txt")
        
        # Assert
        assert result["success"] == False
        assert "error" in result
    
    def test_delete_file_success(self):
        """Test deleting a file."""
        # Arrange
        from backend.tools import starter_tools
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            
            # Create file first
            Path(test_file).touch()
            assert os.path.exists(test_file)
            
            # Act
            result = starter_tools.delete_file(test_file)
            
            # Assert
            assert result["success"] == True
            assert not os.path.exists(test_file)
    
    def test_list_directory_success(self):
        """Test listing directory contents."""
        # Arrange
        from backend.tools import starter_tools
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files
            Path(os.path.join(tmpdir, "file1.txt")).touch()
            Path(os.path.join(tmpdir, "file2.txt")).touch()
            
            # Act
            result = starter_tools.list_directory(tmpdir)
            
            # Assert
            assert result["success"] == True
            items = result["data"]["items"]
            assert "file1.txt" in items
            assert "file2.txt" in items


class TestMemoryTools:
    """Test memory/data storage tools."""
    
    def test_remember_data_success(self):
        """Test remembering data."""
        # Arrange
        from backend.tools import starter_tools
        
        # Act
        result = starter_tools.remember_data("test_key", "test_value")
        
        # Assert
        assert result["success"] == True
        assert result.get("message") is not None
    
    def test_recall_data_success(self):
        """Test recalling data."""
        # Arrange
        from backend.tools import starter_tools
        
        # First store data
        starter_tools.remember_data("recall_test_key", "recall_test_value")
        
        # Act
        result = starter_tools.recall_data("recall_test_key")
        
        # Assert
        assert result["success"] == True
        if "value" in result.get("data", {}):
            assert result["data"]["value"] == "recall_test_value"
    
    def test_recall_nonexistent_key(self):
        """Test recalling non-existent key."""
        # Arrange
        from backend.tools import starter_tools
        
        # Act
        result = starter_tools.recall_data("nonexistent_key_xyz")
        
        # Assert
        # Should either return success=False or empty/null value
        success = result.get("success", False)
        has_value = "value" in result.get("data", {})
        # Either it fails or returns empty
        assert success == False or not has_value or result["data"]["value"] is None
    
    def test_list_memory(self):
        """Test listing all stored memories."""
        # Arrange
        from backend.tools import starter_tools
        
        # Store a test item
        starter_tools.remember_data("list_test_key", "list_test_value")
        
        # Act
        result = starter_tools.list_memory()
        
        # Assert
        assert result["success"] == True
        assert "facts" in result.get("data", {})
    
    def test_delete_memory_success(self):
        """Test deleting memory entry."""
        # Arrange
        from backend.tools import starter_tools
        
        # Store data first
        starter_tools.remember_data("delete_test_key", "value_to_delete")
        
        # Act
        result = starter_tools.delete_memory("delete_test_key")
        
        # Assert
        assert result["success"] == True


class TestCoreSystemTools:
    """Test core system-level tools."""
    
    def test_take_screenshot_requirements(self):
        """Test that take_screenshot handles PIL dependency."""
        # Arrange
        from backend.tools import starter_tools
        
        # Act: Should not crash even if PIL is not available
        result = starter_tools.take_screenshot()
        
        # Assert: Should return a dict (success or error, but not crash)
        assert isinstance(result, dict)
        assert "success" in result or "error" in result
    
    def test_set_volume_with_valid_level(self):
        """Test setting system volume with valid level."""
        # Arrange
        from backend.tools import starter_tools
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
            # Act
            result = starter_tools.set_volume(50)
            
            # Assert
            assert isinstance(result, dict)
            assert "success" in result or "message" in result
    
    def test_set_volume_with_invalid_level(self):
        """Test setting volume with invalid level."""
        # Arrange
        from backend.tools import starter_tools
        
        # Act: Level out of range
        result = starter_tools.set_volume(150)
        
        # Assert
        assert isinstance(result, dict)
        # Should handle gracefully - either error or clamp value
        assert "success" in result or "error" in result
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test running a shell command."""
        # Arrange
        from backend.tools import starter_tools
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="command output",
            stderr=""
        )
        
        # Act
        result = starter_tools.run_command("echo test")
        
        # Assert
        assert result["success"] == True
        assert "command output" in result.get("data", {}).get("stdout", "")
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test running a command that fails."""
        # Arrange
        from backend.tools import starter_tools
        
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="command not found"
        )
        
        # Act
        result = starter_tools.run_command("invalid_command_xyz")
        
        # Assert
        assert result["success"] == False
        assert result.get("error") is not None


class TestToolNormalization:
    """Test result normalization across tools."""
    
    def test_all_results_have_success_field(self):
        """Test that all tool results contain 'success' field."""
        # Arrange
        from backend.tools import starter_tools
        
        # Act & Assert: Test several tools
        result1 = starter_tools.list_memory()
        assert "success" in result1
        
        result2 = starter_tools.open_app("")
        assert "success" in result2
        
        result3 = starter_tools.get_running_apps()
        assert "success" in result3
    
    def test_error_results_have_error_field(self):
        """Test that error results contain error information."""
        # Arrange
        from backend.tools import starter_tools
        
        # Act: Trigger an error condition
        result = starter_tools.read_file("/nonexistent/path/file.txt")
        
        # Assert
        assert result["success"] == False
        assert "error" in result or "message" in result
