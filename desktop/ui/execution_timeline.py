from __future__ import annotations

import re
from typing import Dict

from PySide6 import QtCore, QtGui, QtWidgets


TOOL_DISPLAY = {
    "browser.search_google": "Searching Google",
    "file.move_file": "Moving files",
    "system.shutdown": "Shutting down computer",
    "desktop.open_app": "Opening application",
    "desktop.type_text": "Typing text",
    "desktop.click_element": "Clicking element",
    "desktop.press_key": "Pressing key",
    "memory.store": "Remembering info",
    "email.send": "Preparing Email",
    "automation.email_tool.send_email": "Preparing Email",
}

def parse_action_message(desc: str) -> tuple[str, list[str]]:
    # Parse format "tool_name (param=val)" into user-facing action + details.
    base = desc
    params = ""
    if " (" in desc and desc.endswith(")"):
        parts = desc.split(" (", 1)
        tool_name = parts[0]
        params = parts[1][:-1]
        base = tool_name
        
    if base in TOOL_DISPLAY:
        base = TOOL_DISPLAY[base]
    else:
        # Fallback humanization: "domain.action_name" -> "Domain action name"
        parts = base.split(".")
        if len(parts) >= 2:
            domain = parts[0].capitalize()
            action = parts[1].replace("_", " ")
            if action == "open":
                base = f"Opening {domain}"
            else:
                base = f"{domain} {action}"
        else:
            base = base.replace("_", " ").capitalize()

    details: list[str] = []
    if params:
        recipient_match = re.search(r"recipient=['\"]?([^,'\"]+)", params)
        if recipient_match:
            details.append(f"Recipient: {recipient_match.group(1)}")

        subject_match = re.search(r"subject=['\"]?([^,'\"]+)", params)
        if subject_match:
            details.append(f"Subject: {subject_match.group(1)}")

        app_match = re.search(r"app(?:_name)?=['\"]?([^,'\"]+)", params)
        if app_match and "Open" in base:
            details.append(f"Application: {app_match.group(1)}")

    return base, details

class ExecutionTimeline(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.is_expanded = False
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(0)
        
        # Header Button
        self.btn_toggle = QtWidgets.QPushButton("▶ Assistant Actions")
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                text-align: left;
                background: transparent;
                color: #d1d5db;
                font-weight: 700;
                font-size: 13px;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                color: #e5e7eb;
            }
        """)
        self.btn_toggle.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.clicked.connect(self._toggle_expand)
        
        layout.addWidget(self.btn_toggle)

        self.list_container = QtWidgets.QFrame()
        self.list_container.setStyleSheet("QFrame { background: #161b22; border-radius: 8px; border: 1px solid #374151; margin-top: 4px; }")
        
        list_layout = QtWidgets.QVBoxLayout(self.list_container)
        list_layout.setContentsMargins(4, 4, 4, 4)

        self.list = QtWidgets.QListWidget()
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.list.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.list.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.list.setStyleSheet("""
            QListWidget { background: transparent; padding: 4px; }
            QListWidget::item { border-bottom: 1px solid #1f2937; padding: 8px 4px; margin-bottom: 4px; }
            QListWidget::item:last { border-bottom: none; }
        """)
        self.list.setWordWrap(True)

        list_layout.addWidget(self.list)
        layout.addWidget(self.list_container)
        
        self.list_container.hide() # Collapsed initially

        self._by_step: Dict[int, QtWidgets.QListWidgetItem] = {}

    def _toggle_expand(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.btn_toggle.setText("▼ Assistant Actions")
            self.list_container.show()
        else:
            self.btn_toggle.setText("▶ Assistant Actions")
            self.list_container.hide()

    def add_action_note(self, title: str, details: list[str] | None = None, status: str = "running") -> None:
        if not self.is_expanded:
            self._toggle_expand()
        self._upsert_item(step=0, title=title, details=details or [], status=status)

    def clear(self) -> None:
        self.list.clear()
        self._by_step.clear()

    def upsert_step(self, data: dict) -> None:
        step = int((data or {}).get("step") or 0)
        desc = str((data or {}).get("description") or "")
        status = str((data or {}).get("status") or "running")

        # Auto-expand if a new task begins
        if not self.is_expanded and status == "running":
            self._toggle_expand()

        title, parsed_details = parse_action_message(desc)

        if status == "pending":
            parsed_details = parsed_details + ["Waiting for confirmation..."]

        self._upsert_item(step=step, title=title, details=parsed_details, status=status)

    def _upsert_item(self, step: int, title: str, details: list[str], status: str) -> None:
        icon = "⏳"
        color = QtGui.QColor("#9ca3af")
        if status == "running":
            color = QtGui.QColor("#fbbf24")
            icon = "⏳"
        elif status == "done":
            color = QtGui.QColor("#10b981")
            icon = "✔"
        elif status == "pending":
            color = QtGui.QColor("#60a5fa")
            icon = "⏳"
        elif status == "error":
            color = QtGui.QColor("#ef4444")
            icon = "⚠"

        lines = [f"{icon} {title}"]
        lines.extend(details)
        label = "\n".join(lines)

        if step and step in self._by_step:
            item = self._by_step[step]
            item.setText(label)
        else:
            item = QtWidgets.QListWidgetItem(label)
            self.list.addItem(item)
            if step:
                self._by_step[step] = item

        item.setForeground(color)
        item.setSizeHint(item.sizeHint())
        self.list.scrollToBottom()
