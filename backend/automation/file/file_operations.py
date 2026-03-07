# backend/automation/file/file_operations.py

import os
import shutil
from send2trash import send2trash
from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import error_handler, AutomationError
from backend.config.logger import logger
from backend.automation.file.delete_history import delete_history


class FileOpenTool(BaseTool):
    name = "file.open"
    description = "Open a file by full path"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, path: str):
        """Open a file with comprehensive error handling"""
        
        def _open():
            # Validate path
            if not path or not path.strip():
                raise ValueError("File path cannot be empty")
            
            # Normalize path
            normalized_path = os.path.normpath(path)
            
            # Check if file exists
            if not os.path.exists(normalized_path):
                logger.warning(f"File not found: {normalized_path}")
                raise FileNotFoundError(
                    f"File not found: {normalized_path}",
                )
            
            # Check if it's actually a file (not a directory)
            if not os.path.isfile(normalized_path):
                logger.warning(f"Path is not a file: {normalized_path}")
                raise ValueError(
                    f"{normalized_path} is not a file"
                )
            
            # Open the file
            logger.info(f"Opening file: {normalized_path}")
            
            try:
                os.startfile(normalized_path)
            except Exception as e:
                logger.error(f"Failed to open file {normalized_path}: {e}")
                raise AutomationError(
                    str(e),
                    f"I couldn't open the file. Please make sure you have an application to open {os.path.splitext(normalized_path)[1]} files."
                )

            return {
                "status": "success",
                "message": f"Opened {os.path.basename(normalized_path)}",
                "data": {"path": normalized_path}
            }
        
        return error_handler.wrap_automation(
            func=_open,
            operation_name="Open File",
            context={"path": path}
        )


class FileCreateTool(BaseTool):
    name = "file.create"
    description = "Create a file"
    risk_level = "medium"
    requires_confirmation = False

    def execute(self, path: str):
        """Create a file with comprehensive error handling"""
        
        def _create():
            # Validate path
            if not path or not path.strip():
                raise ValueError("File path cannot be empty")
            
            # Normalize path
            normalized_path = os.path.normpath(path)
            
            # Check if file already exists
            if os.path.exists(normalized_path):
                logger.warning(f"File already exists: {normalized_path}")
                raise FileExistsError(
                    f"File already exists: {normalized_path}"
                )
            
            # Ensure parent directory exists
            parent_dir = os.path.dirname(normalized_path)
            if parent_dir and not os.path.exists(parent_dir):
                logger.info(f"Creating parent directory: {parent_dir}")
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                except Exception as e:
                    logger.error(f"Failed to create parent directory: {e}")
                    raise AutomationError(
                        str(e),
                        f"I couldn't create the directory structure for the file."
                    )
            
            # Create the file
            logger.info(f"Creating file: {normalized_path}")
            
            try:
                with open(normalized_path, "w") as f:
                    f.write("")
            except Exception as e:
                logger.error(f"Failed to create file {normalized_path}: {e}")
                raise AutomationError(
                    str(e),
                    f"I couldn't create the file. Please check if you have write permissions."
                )

            return {
                "status": "success",
                "message": f"File created: {os.path.basename(normalized_path)}",
                "data": {"path": normalized_path}
            }
        
        return error_handler.wrap_automation(
            func=_create,
            operation_name="Create File",
            context={"path": path}
        )


class FileDeleteTool(BaseTool):
    name = "file.delete"
    description = "Delete a file (moves to Recycle Bin)"
    risk_level = "high"
    requires_confirmation = True

    def execute(self, path: str):
        try:
            if not os.path.exists(path):
                logger.warning(f"File delete failed - file not found: {path}")
                return {"status": "error", "message": "File not found", "data": {}}

            # Get file info before deletion
            file_size = os.path.getsize(path)
            
            # Move to Recycle Bin instead of permanent delete
            send2trash(path)
            
            # Add to delete history for undo capability
            entry_id = delete_history.add_entry(
                path=path,
                item_type="file",
                metadata={"size": file_size}
            )
            
            # Log the deletion
            logger.info(f"File moved to Recycle Bin: {path} (size: {file_size} bytes, entry_id: {entry_id})")

            return {
                "status": "success",
                "message": f"Moved {path} to Recycle Bin (can be restored)",
                "data": {"entry_id": entry_id, "path": path}
            }

        except Exception as e:
            logger.error(f"File delete error for {path}: {str(e)}")
            return {"status": "error", "message": str(e), "data": {}}


class FileMoveTool(BaseTool):
    name = "file.move"
    description = "Move file to new location"
    risk_level = "medium"
    requires_confirmation = True

    def execute(self, source: str, destination: str):
        """Move file with comprehensive error handling"""
        
        def _move():
            # Validate paths
            if not source or not source.strip():
                raise ValueError("Source path cannot be empty")
            
            if not destination or not destination.strip():
                raise ValueError("Destination path cannot be empty")
            
            # Normalize paths
            normalized_source = os.path.normpath(source)
            normalized_dest = os.path.normpath(destination)
            
            # Check if source exists
            if not os.path.exists(normalized_source):
                logger.warning(f"Source file not found: {normalized_source}")
                raise FileNotFoundError(
                    f"Source file not found: {normalized_source}"
                )
            
            # Check if destination already exists
            if os.path.exists(normalized_dest):
                logger.warning(f"Destination already exists: {normalized_dest}")
                raise FileExistsError(
                    f"Destination already exists: {normalized_dest}"
                )
            
            # Ensure destination directory exists
            dest_dir = os.path.dirname(normalized_dest)
            if dest_dir and not os.path.exists(dest_dir):
                logger.info(f"Creating destination directory: {dest_dir}")
                try:
                    os.makedirs(dest_dir, exist_ok=True)
                except Exception as e:
                    logger.error(f"Failed to create destination directory: {e}")
                    raise AutomationError(
                        str(e),
                        "I couldn't create the destination directory."
                    )
            
            # Move the file
            logger.info(f"Moving file from {normalized_source} to {normalized_dest}")
            
            try:
                shutil.move(normalized_source, normalized_dest)
            except Exception as e:
                logger.error(f"Failed to move file: {e}")
                raise AutomationError(
                    str(e),
                    "I couldn't move the file. Please check permissions and disk space."
                )

            return {
                "status": "success",
                "message": f"File moved successfully to {os.path.basename(normalized_dest)}",
                "data": {"source": normalized_source, "destination": normalized_dest}
            }
        
        return error_handler.wrap_automation(
            func=_move,
            operation_name="Move File",
            context={"source": source, "destination": destination}
        )


class FileDeleteHistoryTool(BaseTool):
    name = "file.delete_history"
    description = "View recent file/folder deletion history"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, limit: int = 10):
        try:
            recent_deletes = delete_history.get_recent_deletes(limit)
            
            if not recent_deletes:
                return {
                    "status": "success",
                    "message": "No recent deletions found",
                    "data": {"deletes": []}
                }
            
            # Format the history for display
            formatted_history = []
            for entry in recent_deletes:
                formatted_history.append({
                    "id": entry.get("id"),
                    "path": entry.get("path"),
                    "type": entry.get("type"),
                    "timestamp": entry.get("timestamp"),
                    "in_recycle_bin": entry.get("in_recycle_bin", True),
                    "size": entry.get("metadata", {}).get("size", 0)
                })
            
            logger.info(f"Retrieved {len(formatted_history)} recent delete entries")
            
            return {
                "status": "success",
                "message": f"Found {len(formatted_history)} recent deletions",
                "data": {
                    "deletes": formatted_history,
                    "note": "Items are in Recycle Bin and can be manually restored"
                }
            }

        except Exception as e:
            logger.error(f"Error retrieving delete history: {str(e)}")
            return {"status": "error", "message": str(e), "data": {}}


class FileOpenRecycleBinTool(BaseTool):
    name = "file.open_recycle_bin"
    description = "Open the Windows Recycle Bin to manually restore files"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        try:
            # Open Recycle Bin using Windows shell command
            import subprocess
            subprocess.Popen(['explorer', 'shell:RecycleBinFolder'])
            
            logger.info("Opened Recycle Bin for manual file restoration")
            
            return {
                "status": "success",
                "message": "Recycle Bin opened. You can manually restore deleted files from there.",
                "data": {}
            }

        except Exception as e:
            logger.error(f"Error opening Recycle Bin: {str(e)}")
            return {"status": "error", "message": str(e), "data": {}}

