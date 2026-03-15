from __future__ import annotations

from PySide6 import QtWidgets


class ConfirmationDialog(QtWidgets.QDialog):
    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm action")
        self.setModal(True)
        self.setMinimumWidth(520)

        label = QtWidgets.QLabel(message)
        label.setWordWrap(True)

        btn_yes = QtWidgets.QPushButton("Approve")
        btn_no = QtWidgets.QPushButton("Deny")
        btn_yes.clicked.connect(self.accept)
        btn_no.clicked.connect(self.reject)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(btn_no)
        btn_row.addWidget(btn_yes)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(label)
        layout.addSpacing(8)
        layout.addLayout(btn_row)

    @property
    def approved(self) -> bool:
        return self.result() == QtWidgets.QDialog.DialogCode.Accepted
