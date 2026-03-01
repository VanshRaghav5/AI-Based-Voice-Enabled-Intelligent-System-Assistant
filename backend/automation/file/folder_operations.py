# backend/automation/file/folder_operations.py

import os
import shutil
from send2trash import send2trash
from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import error_handler, AutomationError
from backend.config.logger import logger
from backend.automation.file.delete_history import delete_history


class FolderCreateTool(BaseTool):
    name = "folder.create"
    description = "Create a folder"
    risk_level = "medium"
    requires_confirmation = False

    def execute(self, path: str):
        """Create a folder with comprehensive error handling"""
        
        def _create():
            # Validate path
            if not path or not path.strip():
                raise ValueError("Folder path cannot be empty")
            
            # Normalize path
            normalized_path = os.path.normpath(path)
            
            # Check if folder already exists
            if os.path.exists(normalized_path):
                if os.path.isdir(normalized_path):
                    logger.info(f"Folder already exists: {normalized_path}")
                    return {
                        "status": "success",
                        "message": f"Folder already exists: {os.path.basename(normalized_path)}",
                        "data": {"path": normalized_path, "already_existed": True}
                    }
                else:
                    logger.warning(f"Path exists but is not a folder: {normalized_path}")
                    raise FileExistsError(
                        f"A file already exists at: {normalized_path}"
                    )
            
            # Create the folder
            logger.info(f"Creating folder: {normalized_path}")
            
            try:
                os.makedirs(normalized_path, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create folder {normalized_path}: {e}")
                raise AutomationError(
                    str(e),
                    "I couldn't create the folder. Please check if you have write permissions."
                )

            return {
                "status": "success",
                "message": f"Folder created: {os.path.basename(normalized_path)}",
                "data": {"path": normalized_path}
            }
        
        return error_handler.wrap_automation(
            func=_create,
            operation_name="Create Folder",
            context={"path": path}
        )


class FolderDeleteTool(BaseTool):
    name = "folder.delete"
    description = "Delete a folder (moves to Recycle Bin)"
    risk_level = "high"
    requires_confirmation = True

    def execute(self, path: str):
        try:
            if not os.path.exists(path):
                logger.warning(f"Folder delete failed - folder not found: {path}")
                return {"status": "error", "message": "Folder not found", "data": {}}

            # Get folder info before deletion
            folder_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, _, filenames in os.walk(path)
                for filename in filenames
            )
            
            # Move to Recycle Bin instead of permanent delete
            send2trash(path)
            
            # Add to delete history for undo capability
            entry_id = delete_history.add_entry(
                path=path,
                item_type="folder",
                metadata={"size": folder_size}
            )
            
            # Log the deletion
            logger.info(f"Folder moved to Recycle Bin: {path} (size: {folder_size} bytes, entry_id: {entry_id})")

            return {
                "status": "success",
                "message": f"Moved {path} to Recycle Bin (can be restored)",
                "data": {"entry_id": entry_id, "path": path}
            }

        except Exception as e:
            logger.error(f"Folder delete error for {path}: {str(e)}")
            return {"status": "error", "message": str(e), "data": {}}
