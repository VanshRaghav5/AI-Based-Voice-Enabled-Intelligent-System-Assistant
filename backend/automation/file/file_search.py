# backend/automation/file/file_search.py

import os
from backend.automation.base_tool import BaseTool


class FileSearchTool(BaseTool):
    name = "file.search"
    description = "Search file by name"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, filename: str, root: str = "C:\\"):
        try:
            matches = []

            for root_dir, _, files in os.walk(root):
                for file in files:
                    if filename.lower() in file.lower():
                        matches.append(os.path.join(root_dir, file))

                        if len(matches) >= 5:
                            break

                if len(matches) >= 5:
                    break

            if not matches:
                return {"status": "error", "message": "File not found", "data": {}}

            return {
                "status": "success",
                "message": f"Found {len(matches)} file(s)",
                "data": {"matches": matches}
            }

        except Exception as e:
            return {"status": "error", "message": str(e), "data": {}}
