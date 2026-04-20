# backend/automation/coding/vscode_tool.py

import os
import shutil
import subprocess
from typing import Dict, Any

from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import error_handler, AutomationError
from backend.config.logger import logger


def _find_code_cli() -> str:
    """Locate the VS Code CLI binary.

    Returns the path to ``code`` (or ``code.cmd`` on Windows) if found,
    otherwise raises an ``AutomationError`` with helpful guidance.
    """
    code_path = shutil.which("code") or shutil.which("code.cmd")
    if code_path:
        return code_path

    # Common Windows install locations.
    common_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft VS Code\bin\code.cmd"),
    ]
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate

    raise AutomationError(
        "VS Code CLI not found on PATH",
        "I could not find VS Code. Please install it or make sure the 'code' command is on your PATH.",
    )


class VSCodeOpenProjectTool(BaseTool):
    name = "code.open_project"
    description = "Open a project folder or file in VS Code"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, path: str = ".") -> Dict[str, Any]:
        resolved = os.path.abspath(path)

        def _open():
            if not os.path.exists(resolved):
                raise AutomationError(
                    f"Path does not exist: {resolved}",
                    f"I could not find {resolved}. Please check the path and try again.",
                )

            code_bin = _find_code_cli()
            logger.info(f"[VSCode] Opening project: {resolved} (cli: {code_bin})")

            try:
                subprocess.Popen([code_bin, resolved], shell=False)
            except Exception as exc:
                logger.error(f"[VSCode] Failed to launch VS Code: {exc}")
                raise AutomationError(
                    str(exc),
                    "I could not open VS Code. Please try opening it manually.",
                )

            display_name = os.path.basename(resolved) or resolved
            return {
                "status": "success",
                "message": f"Opening {display_name} in VS Code",
                "data": {"path": resolved},
            }

        return error_handler.wrap_automation(
            func=_open,
            operation_name="Open VS Code Project",
            context={"path": resolved},
        )
