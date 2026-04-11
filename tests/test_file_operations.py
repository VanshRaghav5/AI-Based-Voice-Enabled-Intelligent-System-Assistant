"""Tests for File Operations with mocking."""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestFileCreateTool:
    """Test file creation with mocking."""
    
    @patch('backend.tools.file.file_operations.os.path.exists')
    @patch('backend.tools.file.file_operations.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_file_create_success(self, mock_file, mock_makedirs, mock_exists):
        """Test successful file creation (mocked)."""
        # Arrange
        mock_exists.return_value = False
        
        from backend.tools.file.file_operations import FileCreateTool
        tool = FileCreateTool()
        
        # Act
        result = tool.execute(path="C:/test/newfile.txt")
        
        # Assert
        assert result["status"] == "success"
        mock_file.assert_called_once()
    
    @patch('backend.tools.file.file_operations.os.path.exists')
    def test_file_create_already_exists(self, mock_exists):
        """Test file creation when file already exists."""
        # Arrange
        mock_exists.return_value = True
        
        from backend.tools.file.file_operations import FileCreateTool
        tool = FileCreateTool()
        
        # Act
        result = tool.execute(path="C:/test/existing.txt")
        
        # Assert
        assert result["status"] == "error"
        assert "already exists" in result["message"].lower()
    
    @patch('backend.tools.file.file_operations.os.path.exists')
    @patch('backend.tools.file.file_operations.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_file_create_with_parent_directory(self, mock_file, mock_makedirs, mock_exists):
        """Test file creation creates parent directories."""
        # Arrange
        mock_exists.side_effect = [False, False]  # File doesn't exist, parent doesn't exist
        
        from backend.tools.file.file_operations import FileCreateTool
        tool = FileCreateTool()
        
        # Act
        result = tool.execute(path="C:/new/path/file.txt")
        
        # Assert
        assert result["status"] == "success"
        # Parent directory should be created
        mock_makedirs.assert_called()
    
    def test_file_create_invalid_path(self):
        """Test file creation with invalid/empty path."""
        # Arrange
        from backend.tools.file.file_operations import FileCreateTool
        tool = FileCreateTool()
        
        # Act
        result = tool.execute(path="")
        
        # Assert
        assert result["status"] == "error"


class TestFileDeleteTool:
    """Test file deletion with mocking (no real deletes)."""
    
    @patch('backend.tools.file.file_operations.os.path.exists')
    @patch('backend.tools.file.file_operations.os.path.getsize')
    @patch('backend.tools.file.file_operations.send2trash')
    @patch('backend.tools.file.file_operations.delete_history')
    def test_file_delete_success(self, mock_history, mock_trash, mock_getsize, mock_exists):
        """Test successful file deletion to Recycle Bin (mocked)."""
        # Arrange
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        mock_history.add_entry.return_value = "entry_123"
        
        from backend.tools.file.file_operations import FileDeleteTool
        tool = FileDeleteTool()
        
        # Act
        result = tool.execute(path="C:/test/deleteme.txt")
        
        # Assert
        assert result["status"] == "success"
        assert "Recycle Bin" in result["message"]
        mock_trash.assert_called_once_with("C:/test/deleteme.txt")
        mock_history.add_entry.assert_called_once()
    
    @patch('backend.tools.file.file_operations.os.path.exists')
    def test_file_delete_not_found(self, mock_exists):
        """Test deleting non-existent file."""
        # Arrange
        mock_exists.return_value = False
        
        from backend.tools.file.file_operations import FileDeleteTool
        tool = FileDeleteTool()
        
        # Act
        result = tool.execute(path="C:/test/nonexistent.txt")
        
        # Assert
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()
    
    @patch('backend.tools.file.file_operations.os.path.exists')
    @patch('backend.tools.file.file_operations.os.path.getsize')
    @patch('backend.tools.file.file_operations.send2trash')
    def test_file_delete_logs_operation(self, mock_trash, mock_getsize, mock_exists):
        """Test that file deletion is logged."""
        # Arrange
        mock_exists.return_value = True
        mock_getsize.return_value = 2048
        
        from backend.tools.file.file_operations import FileDeleteTool
        tool = FileDeleteTool()
        
        with patch('backend.tools.file.file_operations.logger') as mock_logger:
            # Act
            result = tool.execute(path="C:/test/file.txt")
            
            # Assert
            assert result["status"] == "success"
            mock_logger.info.assert_called()


class TestFileMoveTool:
    """Test file move operations with mocking."""
    
    @patch('backend.tools.file.file_operations.os.path.exists')
    @patch('backend.tools.file.file_operations.os.makedirs')
    @patch('backend.tools.file.file_operations.shutil.move')
    def test_file_move_success(self, mock_move, mock_makedirs, mock_exists):
        """Test successful file move (mocked)."""
        # Arrange
        mock_exists.side_effect = [True, False, True]  # Source exists, dest doesn't, dest dir exists
        
        from backend.tools.file.file_operations import FileMoveTool
        tool = FileMoveTool()
        
        # Act
        result = tool.execute(source="C:/old/file.txt", destination="C:/new/file.txt")
        
        # Assert
        assert result["status"] == "success"
        mock_move.assert_called_once()
    
    @patch('backend.tools.file.file_operations.os.path.exists')
    def test_file_move_source_not_found(self, mock_exists):
        """Test moving non-existent file."""
        # Arrange
        mock_exists.return_value = False
        
        from backend.tools.file.file_operations import FileMoveTool
        tool = FileMoveTool()
        
        # Act
        result = tool.execute(source="C:/old/missing.txt", destination="C:/new/file.txt")
        
        # Assert
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()
    
    @patch('backend.tools.file.file_operations.os.path.exists')
    def test_file_move_destination_exists(self, mock_exists):
        """Test moving to existing destination."""
        # Arrange
        mock_exists.side_effect = [True, True]  # Both source and dest exist
        
        from backend.tools.file.file_operations import FileMoveTool
        tool = FileMoveTool()
        
        # Act
        result = tool.execute(source="C:/old/file.txt", destination="C:/new/file.txt")
        
        # Assert
        assert result["status"] == "error"
        assert "already exists" in result["message"].lower()


class TestFolderOperations:
    """Test folder operations with mocking."""
    
    @patch('backend.tools.file.folder_operations.os.makedirs')
    def test_folder_create_success(self, mock_makedirs):
        """Test successful folder creation (mocked)."""
        # Arrange
        from backend.tools.file.folder_operations import FolderCreateTool
        tool = FolderCreateTool()
        
        # Act
        result = tool.execute(path="C:/test/newfolder")
        
        # Assert
        assert result["status"] == "success"
        mock_makedirs.assert_called_once()
    
    @patch('backend.tools.file.folder_operations.os.path.exists')
    @patch('backend.tools.file.folder_operations.send2trash')
    @patch('backend.tools.file.folder_operations.delete_history')
    def test_folder_delete_success(self, mock_history, mock_trash, mock_exists):
        """Test successful folder deletion (mocked)."""
        # Arrange
        mock_exists.return_value = True
        mock_history.add_entry.return_value = "entry_456"
        
        with patch('backend.tools.file.folder_operations.os.walk') as mock_walk:
            mock_walk.return_value = [
                ("C:/test", [], ["file1.txt", "file2.txt"])
            ]
            
            from backend.tools.file.folder_operations import FolderDeleteTool
            tool = FolderDeleteTool()
            
            # Act
            result = tool.execute(path="C:/test/oldfolder")
            
            # Assert
            assert result["status"] == "success"
            assert "Recycle Bin" in result["message"]
            mock_trash.assert_called_once()
