# backend/automation/file/file_operations.py

import os
import shutil
from backend.automation.base_tool import BaseTool


class FileOpenTool(BaseTool):
    name = "file.open"
    description = "Open a file by full path"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, path: str):
        try:
            if not os.path.exists(path):
                return {"status": "error", "message": "File not found", "data": {}}

            os.startfile(path)

            return {"status": "success", "message": f"Opened {path}", "data": {}}

        except Exception as e:
            return {"status": "error", "message": str(e), "data": {}}


class FileCreateTool(BaseTool):
    name = "file.create"
    description = "Create a file"
    risk_level = "medium"
    requires_confirmation = False

    def execute(self, path: str):
        try:
            with open(path, "w") as f:
                f.write("")

            return {"status": "success", "message": f"File created at {path}", "data": {}}

        except Exception as e:
            return {"status": "error", "message": str(e), "data": {}}


class FileDeleteTool(BaseTool):
    name = "file.delete"
    description = "Delete a file"
    risk_level = "high"
    requires_confirmation = True

    def execute(self, path: str):
        try:
            if not os.path.exists(path):
                return {"status": "error", "message": "File not found", "data": {}}

            os.remove(path)

            return {"status": "success", "message": f"Deleted {path}", "data": {}}

        except Exception as e:
            return {"status": "error", "message": str(e), "data": {}}


class FileMoveTool(BaseTool):
    name = "file.move"
    description = "Move file to new location"
    risk_level = "medium"
    requires_confirmation = True

    def execute(self, source: str, destination: str):
        try:
            if not os.path.exists(source):
                return {"status": "error", "message": "Source file not found", "data": {}}

            shutil.move(source, destination)

            return {"status": "success", "message": "File moved successfully", "data": {}}

        except Exception as e:
            return {"status": "error", "message": str(e), "data": {}}
