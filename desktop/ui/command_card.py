from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets

class CommandCard(QtWidgets.QFrame):
    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            CommandCard {
                background: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
            QLabel {
                font-family: 'Segoe UI', Arial;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        lbl_title = QtWidgets.QLabel(title)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #f3f4f6;")
        layout.addWidget(lbl_title)
        
        lbl_content = QtWidgets.QLabel(content)
        lbl_content.setStyleSheet("font-size: 13px; color: #d1d5db;")
        lbl_content.setWordWrap(True)
        layout.addWidget(lbl_content)
        
        # Add a subtle shadow
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Adjust size logic for content
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)


class EmailCommandCard(QtWidgets.QFrame):
    send_requested = QtCore.Signal(dict)
    edit_requested = QtCore.Signal(dict)

    def __init__(self, recipient: str = "", subject: str = "", body: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background: #1f2937; border-radius: 12px; border: 1px solid #374151; }"
            "QLabel { color: #e5e7eb; font-family: 'Segoe UI', Arial; }"
            "QLineEdit, QTextEdit {"
            " background: #111827; color: #e5e7eb; border: 1px solid #334155; border-radius: 8px; padding: 6px;"
            "}"
            "QPushButton { border-radius: 8px; padding: 8px 14px; font-weight: 600; }"
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        lbl_title = QtWidgets.QLabel("Email")
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f3f4f6;")
        layout.addWidget(lbl_title)

        self.to_input = QtWidgets.QLineEdit(recipient)
        self.subject_input = QtWidgets.QLineEdit(subject)
        self.body_input = QtWidgets.QTextEdit()
        self.body_input.setFixedHeight(90)
        self.body_input.setPlainText(body)

        layout.addWidget(QtWidgets.QLabel("To:"))
        layout.addWidget(self.to_input)
        layout.addWidget(QtWidgets.QLabel("Subject:"))
        layout.addWidget(self.subject_input)
        layout.addWidget(QtWidgets.QLabel("Body:"))
        layout.addWidget(self.body_input)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)

        btn_send = QtWidgets.QPushButton("Send")
        btn_send.setStyleSheet("QPushButton { background: #3b82f6; color: white; } QPushButton:hover { background: #2563eb; }")
        btn_edit = QtWidgets.QPushButton("Edit")
        btn_edit.setStyleSheet("QPushButton { background: #334155; color: #e5e7eb; } QPushButton:hover { background: #475569; }")

        btn_send.clicked.connect(lambda: self.send_requested.emit(self.get_payload()))
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.get_payload()))

        row.addWidget(btn_send)
        row.addWidget(btn_edit)
        row.addStretch(1)
        layout.addLayout(row)

        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)

    def get_payload(self) -> dict:
        return {
            "recipient": self.to_input.text().strip(),
            "subject": self.subject_input.text().strip(),
            "body": self.body_input.toPlainText().strip(),
        }
