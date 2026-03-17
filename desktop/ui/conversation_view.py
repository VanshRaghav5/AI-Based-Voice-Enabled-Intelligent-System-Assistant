from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from desktop.ui.command_card import EmailCommandCard
from desktop.ui.message_bubble import AssistantBubble, SystemBubble, UserBubble

class QuickSuggestions(QtWidgets.QWidget):
    suggestion_clicked = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(12)
        
        lbl = QtWidgets.QLabel("Try asking:")
        lbl.setStyleSheet("color: #9ca3af; font-size: 14px; font-weight: bold; font-family: 'Segoe UI', Arial;")
        lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        
        suggestions = [
            "Send email",
            "Schedule meeting",
            "Open Spotify",
            "Check today's tasks"
        ]
        
        for i, text in enumerate(suggestions):
            btn = QtWidgets.QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background: #1f2937; color: #e5e7eb; border-radius: 12px; padding: 10px; font-size: 13px; border: 1px solid #374151;
                }
                QPushButton:hover {
                    background: #374151; border: 1px solid #4b5563;
                }
            """)
            btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, t=text: self.suggestion_clicked.emit(t))
            grid.addWidget(btn, i // 2, i % 2)
            
        layout.addLayout(grid)

class TypingIndicator(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QWidget { background: transparent; }")

        card = QtWidgets.QFrame(self)
        card.setStyleSheet(
            "QFrame { background: #131b25; border: 1px solid #263447; border-radius: 12px; }"
        )

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 6, 0, 8)
        root.addWidget(card)

        layout = QtWidgets.QHBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        self.icon_label = QtWidgets.QLabel("◐")
        self.icon_label.setStyleSheet("color: #7dd3fc; font-size: 16px; font-weight: 700;")

        text_col = QtWidgets.QVBoxLayout()
        text_col.setSpacing(1)
        self.label = QtWidgets.QLabel("OmniAssist is thinking")
        self.label.setStyleSheet("color: #dbeafe; font-size: 13px; font-weight: 600;")
        self.sub_label = QtWidgets.QLabel("...")
        self.sub_label.setStyleSheet("color: #93c5fd; font-size: 12px; letter-spacing: 1px;")
        text_col.addWidget(self.label)
        text_col.addWidget(self.sub_label)

        layout.addWidget(self.icon_label)
        layout.addLayout(text_col)
        layout.addStretch()

        self._frames = ["◐", "◓", "◑", "◒"]
        self._frame_idx = 0
        self._dot_frames = [".", "..", "...", "...."]
        self._dot_idx = 0

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._animate)

        self._opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._pulse = QtCore.QPropertyAnimation(self._opacity_effect, b"opacity")
        self._pulse.setDuration(900)
        self._pulse.setLoopCount(-1)
        self._pulse.setKeyValueAt(0.0, 0.72)
        self._pulse.setKeyValueAt(0.5, 1.0)
        self._pulse.setKeyValueAt(1.0, 0.72)
    
    def start(self):
        self.timer.start(140)
        self._pulse.start()
        self.show()

    def stop(self):
        self.timer.stop()
        self._pulse.stop()
        self.hide()

    def _animate(self):
        self._frame_idx = (self._frame_idx + 1) % len(self._frames)
        self._dot_idx = (self._dot_idx + 1) % len(self._dot_frames)
        self.icon_label.setText(self._frames[self._frame_idx])
        self.sub_label.setText(self._dot_frames[self._dot_idx])


class ConfirmationPrompt(QtWidgets.QFrame):
    decision_made = QtCore.Signal(bool)

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background: #1a2330; border: 1px solid #2e3a4b; border-radius: 10px; }"
            "QLabel { color: #dbeafe; font-size: 13px; }"
            "QPushButton { border-radius: 8px; padding: 7px 14px; font-weight: 600; }"
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        label = QtWidgets.QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_confirm = QtWidgets.QPushButton("Confirm")
        self.btn_confirm.setStyleSheet(
            "QPushButton { background: #3b82f6; color: white; } QPushButton:hover { background: #2563eb; }"
        )
        self.btn_cancel = QtWidgets.QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(
            "QPushButton { background: #334155; color: #e5e7eb; } QPushButton:hover { background: #475569; }"
        )
        self.btn_confirm.clicked.connect(lambda: self._emit_decision(True))
        self.btn_cancel.clicked.connect(lambda: self._emit_decision(False))

        btn_row.addWidget(self.btn_confirm)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _emit_decision(self, approved: bool):
        self.btn_confirm.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.decision_made.emit(approved)

class ConversationView(QtWidgets.QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.viewport().setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")

        self.container = QtWidgets.QWidget()
        self.container.setStyleSheet("background: transparent;")
        
        self.layout_ = QtWidgets.QVBoxLayout(self.container)
        self.layout_.setContentsMargins(10, 10, 10, 10)
        self.layout_.setSpacing(6)
        
        self.typing_indicator = TypingIndicator()
        self.typing_indicator.hide()
        
        self.suggestions = QuickSuggestions()
        self.layout_.addWidget(self.suggestions)
        
        self.layout_.addWidget(self.typing_indicator)
        self.layout_.addStretch()

        self.setWidget(self.container)

    def _add(self, text: str, is_user: bool = False, is_system: bool = False) -> None:
        if not self.suggestions.isHidden():
            self.suggestions.hide()

        if is_system:
            bubble = SystemBubble(text)
        elif is_user:
            bubble = UserBubble(text)
        else:
            bubble = AssistantBubble(text)
        
        count = self.layout_.count()
        # Insert before the typing indicator and the stretch
        self.layout_.insertWidget(count - 2, bubble)
        
        QtCore.QTimer.singleShot(50, self._scroll_to_bottom)

    def show_thinking(self):
        self.typing_indicator.start()
        QtCore.QTimer.singleShot(50, self._scroll_to_bottom)

    def hide_thinking(self):
        self.typing_indicator.stop()

    def _scroll_to_bottom(self):
        vbar = self.verticalScrollBar()
        vbar.setValue(vbar.maximum())

    def add_user(self, text: str) -> None:
        self._add(text, is_user=True)

    def add_assistant(self, text: str) -> None:
        self._add(text, is_user=False)

    def add_system(self, text: str) -> None:
        self._add(text, is_system=True)

    def add_confirmation_prompt(self, message: str, on_decision) -> None:
        if not self.suggestions.isHidden():
            self.suggestions.hide()

        prompt = ConfirmationPrompt(message)
        if on_decision is not None:
            prompt.decision_made.connect(on_decision)

        count = self.layout_.count()
        self.layout_.insertWidget(count - 2, prompt)
        QtCore.QTimer.singleShot(50, self._scroll_to_bottom)

    def add_email_command_card(self, recipient: str, subject: str, body: str, on_send, on_edit) -> None:
        if not self.suggestions.isHidden():
            self.suggestions.hide()

        card = EmailCommandCard(recipient=recipient, subject=subject, body=body)
        if on_send is not None:
            card.send_requested.connect(on_send)
        if on_edit is not None:
            card.edit_requested.connect(on_edit)

        count = self.layout_.count()
        self.layout_.insertWidget(count - 2, card)
        QtCore.QTimer.singleShot(50, self._scroll_to_bottom)
