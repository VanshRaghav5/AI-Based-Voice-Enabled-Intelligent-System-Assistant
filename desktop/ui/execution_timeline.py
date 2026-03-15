from __future__ import annotations

from typing import Dict

from PySide6 import QtCore, QtWidgets


class ExecutionTimeline(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Execution")

        self.list = QtWidgets.QListWidget()
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.list.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.list)

        self._by_step: Dict[int, QtWidgets.QListWidgetItem] = {}

    def upsert_step(self, data: dict) -> None:
        step = int((data or {}).get("step") or 0)
        desc = str((data or {}).get("description") or "")
        status = str((data or {}).get("status") or "")

        label = f"[{status}] {step}. {desc}" if step else f"[{status}] {desc}"

        if step and step in self._by_step:
            self._by_step[step].setText(label)
        else:
            item = QtWidgets.QListWidgetItem(label)
            self.list.addItem(item)
            if step:
                self._by_step[step] = item
        self.list.scrollToBottom()
