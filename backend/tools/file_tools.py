import os
import subprocess
from backend.tools.error_handler import error_handler, AutomationError
from backend.utils.logger import logger


def create_file(file_path: str) -> dict:
    """
    Creates an empty file at given path with error handling.
    """
    
    def _create():
        if not file_path or not file_path.strip():
            raise ValueError("File path cannot be empty")
        
        normalized_path = os.path.normpath(file_path)
        
        if os.path.exists(normalized_path):
            logger.warning(f"File already exists: {normalized_path}")
            raise FileExistsError(f"File already exists: {normalized_path}")
        
        logger.info(f"Creating file: {normalized_path}")
        
        try:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(normalized_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            with open(normalized_path, "w") as f:
                pass
        except Exception as e:
            logger.error(f"Failed to create file: {e}")
            raise AutomationError(
                str(e),
                "I couldn't create the file. Please check if you have write permissions."
            )

        return {
            "status": "success",
            "message": f"File created at {normalized_path}",
            "data": {"path": normalized_path}
        }
    
    return error_handler.wrap_automation(
        func=_create,
        operation_name="Create File",
        context={"path": file_path}
    )


def delete_file(file_path: str) -> dict:
    """
    Deletes a file if it exists with error handling.
    """
    
    def _delete():
        if not file_path or not file_path.strip():
            raise ValueError("File path cannot be empty")
        
        normalized_path = os.path.normpath(file_path)
        
        if not os.path.exists(normalized_path):
            logger.warning(f"File does not exist: {normalized_path}")
            raise FileNotFoundError("File does not exist")
        
        logger.info(f"Deleting file: {normalized_path}")
        
        try:
            os.remove(normalized_path)
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise AutomationError(
                str(e),
                "I couldn't delete the file. Please check if you have the necessary permissions."
            )

        return {
            "status": "success",
            "message": f"Deleted {normalized_path}",
            "data": {"path": normalized_path}
        }
    
    return error_handler.wrap_automation(
        func=_delete,
        operation_name="Delete File",
        context={"path": file_path}
    )


def open_folder(folder_path: str) -> dict:
    """
    Opens a folder in Windows Explorer with error handling.
    """
    
    def _open():
        if not folder_path or not folder_path.strip():
            raise ValueError("Folder path cannot be empty")
        
        normalized_path = os.path.normpath(folder_path)
        
        if not os.path.exists(normalized_path):
            logger.warning(f"Folder does not exist: {normalized_path}")
            raise FileNotFoundError("Folder does not exist")
        
        if not os.path.isdir(normalized_path):
            logger.warning(f"Path is not a folder: {normalized_path}")
            raise ValueError("Path is not a folder")
        
        logger.info(f"Opening folder: {normalized_path}")
        
        try:
            subprocess.Popen(f'explorer "{normalized_path}"')
        except Exception as e:
            logger.error(f"Failed to open folder: {e}")
            raise AutomationError(
                str(e),
                "I couldn't open the folder in Windows Explorer."
            )

        return {
            "status": "success",
            "message": f"Opening folder {normalized_path}",
            "data": {"path": normalized_path}
        }
    
    return error_handler.wrap_automation(
        func=_open,
        operation_name="Open Folder",
        context={"path": folder_path}
    )
