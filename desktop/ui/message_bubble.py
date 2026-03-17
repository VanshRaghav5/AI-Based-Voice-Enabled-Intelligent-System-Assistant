from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class MessageBubbleWidget(QtWidgets.QFrame):
    def __init__(self, text: str, sender: str, align_right: bool, bubble_style: str, parent=None):
        super().__init__(parent)

        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 4, 0, 8)

        content = QtWidgets.QWidget()
        content.setMaximumWidth(700)
        col = QtWidgets.QVBoxLayout(content)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(4)

        self.sender_label = QtWidgets.QLabel(sender)
        self.sender_label.setStyleSheet(
            "color: #9ca3af; font-size: 12px; font-weight: 700; font-family: 'Segoe UI', Arial;"
        )
        self.sender_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight if align_right else QtCore.Qt.AlignmentFlag.AlignLeft
        )
        col.addWidget(self.sender_label)

        self.bubble_label = QtWidgets.QLabel(text)
        self.bubble_label.setWordWrap(True)
        self.bubble_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.bubble_label.setStyleSheet(bubble_style)
        col.addWidget(self.bubble_label)

        if align_right:
            row.addStretch(1)
            row.addWidget(content, 0)
        else:
            row.addWidget(content, 0)
            row.addStretch(1)

        self.effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.anim = QtCore.QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(260)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()


class UserBubble(MessageBubbleWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(
            text=text,
            sender="User",
            align_right=True,
            bubble_style=(
                "background: #3b82f6; color: #ffffff; "
                "padding: 12px 16px; border-radius: 18px; border-top-right-radius: 5px; "
                "font-size: 14px; font-family: 'Segoe UI', Arial;"
            ),
            parent=parent,
        )


class AssistantBubble(MessageBubbleWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(
            text=text,
            sender="OmniAssist",
            align_right=False,
            bubble_style=(
                "background: #1f2937; color: #f3f4f6; border: 1px solid #374151; "
                "padding: 12px 16px; border-radius: 18px; border-top-left-radius: 5px; "
                "font-size: 14px; font-family: 'Segoe UI', Arial;"
            ),
            parent=parent,
        )


class SystemBubble(QtWidgets.QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 4, 0, 8)
        label = QtWidgets.QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setStyleSheet("background: transparent; color: #6b7280; font-size: 12px; font-style: italic;")
        row.addStretch(1)
        row.addWidget(label)
        row.addStretch(1)
