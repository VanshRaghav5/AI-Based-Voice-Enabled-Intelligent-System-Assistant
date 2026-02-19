import os
import subprocess


def create_file(file_path: str) -> dict:
    """
    Creates an empty file at given path.
    """
    try:
        with open(file_path, "w") as f:
            pass

        return {
            "status": "success",
            "message": f"File created at {file_path}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def delete_file(file_path: str) -> dict:
    """
    Deletes a file if it exists.
    """
    try:
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": "File does not exist."
            }

        os.remove(file_path)

        return {
            "status": "success",
            "message": f"Deleted {file_path}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def open_folder(folder_path: str) -> dict:
    """
    Opens a folder in Windows Explorer.
    """
    try:
        if not os.path.exists(folder_path):
            return {
                "status": "error",
                "message": "Folder does not exist."
            }

        subprocess.Popen(f'explorer "{folder_path}"')

        return {
            "status": "success",
            "message": f"Opening folder {folder_path}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
