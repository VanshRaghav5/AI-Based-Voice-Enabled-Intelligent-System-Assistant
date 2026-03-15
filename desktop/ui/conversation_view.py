from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class ConversationView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.list = QtWidgets.QListWidget()
        self.list.setAlternatingRowColors(False)
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.list.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list)

    def _add(self, prefix: str, text: str) -> None:
        item = QtWidgets.QListWidgetItem(f"{prefix} {text}")
        self.list.addItem(item)
        self.list.scrollToBottom()

    def add_user(self, text: str) -> None:
        self._add("You:", text)

    def add_assistant(self, text: str) -> None:
        self._add("OmniAssist:", text)

    def add_system(self, text: str) -> None:
        self._add("•", text)
