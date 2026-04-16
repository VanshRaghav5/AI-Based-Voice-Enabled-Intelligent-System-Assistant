"""Coding automation tools — project detection, VS Code, terminal."""

from backend.automation.coding.project_detector import ProjectDetectorTool
from backend.automation.coding.vscode_tool import VSCodeOpenProjectTool
from backend.automation.coding.terminal_tool import (
    TerminalRunTool,
    TerminalRunBackgroundTool,
    TerminalKillTool,
    TerminalListRunningTool,
)

__all__ = [
    "ProjectDetectorTool",
    "VSCodeOpenProjectTool",
    "TerminalRunTool",
    "TerminalRunBackgroundTool",
    "TerminalKillTool",
    "TerminalListRunningTool",
]
