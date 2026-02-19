# backend/automation/file/folder_operations.py

import os
import shutil
from backend.automation.base_tool import BaseTool


class FolderCreateTool(BaseTool):
    name = "folder.create"
    description = "Create a folder"
    risk_level = "medium"
    requires_confirmation = False

    def execute(self, path: str):
        try:
            os.makedirs(path, exist_ok=True)

            return {"status": "success", "message": f"Folder created at {path}", "data": {}}

        except Exception as e:
            return {"status": "error", "message": str(e), "data": {}}


class FolderDeleteTool(BaseTool):
    name = "folder.delete"
    description = "Delete a folder"
    risk_level = "high"
    requires_confirmation = True

    def execute(self, path: str):
        try:
            if not os.path.exists(path):
                return {"status": "error", "message": "Folder not found", "data": {}}

            shutil.rmtree(path)

            return {"status": "success", "message": f"Folder deleted at {path}", "data": {}}

        except Exception as e:
            return {"status": "error", "message": str(e), "data": {}}
