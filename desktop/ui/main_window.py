from __future__ import annotations

import re
from PySide6 import QtCore, QtGui, QtWidgets

from desktop.config import DesktopConfig
from desktop.core.assistant_state import AssistantState
from desktop.core.event_bus import EventBus
from desktop.services.api_client import ApiClient
from desktop.services.session_store import SessionStore
from desktop.services.socket_client import SocketClient
from desktop.ui.login_dialog import LoginDialog
from desktop.ui.conversation_view import ConversationView
from desktop.ui.execution_timeline import ExecutionTimeline
from desktop.ui.orb_visualizer import OrbVisualizer
from desktop.ui.particle_field import ParticleField
from desktop.ui.waveform_widget import WaveformWidget
from desktop.ui.settings_dialog import SettingsDialog
from desktop.ui.profile_dialog import ProfileDialog


class CommandHistoryFilter(QtCore.QObject):
    def __init__(self, main_win):
        super().__init__(main_win)
        self.main_win = main_win
        self.history = []
        self.index = -1
        self.current_draft = ""
        
    def add(self, cmd):
        if not self.history or self.history[-1] != cmd:
            self.history.append(cmd)
        self.index = len(self.history)
        
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() == QtCore.Qt.Key.Key_Up:
                if not self.history:
                    return super().eventFilter(obj, event)

                if self.index > 0:
                    if self.index == len(self.history):
                        self.current_draft = self.main_win.input.text()
                    self.index -= 1
                    self.main_win.input.setText(self.history[self.index])
                    self.main_win.input.setCursorPosition(len(self.main_win.input.text()))
                return True
            elif event.key() == QtCore.Qt.Key.Key_Down:
                if not self.history:
                    return super().eventFilter(obj, event)

                if self.index < len(self.history):
                    self.index += 1
                    if self.index == len(self.history):
                        self.main_win.input.setText(self.current_draft)
                    else:
                        self.main_win.input.setText(self.history[self.index])
                    self.main_win.input.setCursorPosition(len(self.main_win.input.text()))
                return True
        return super().eventFilter(obj, event)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, config: DesktopConfig, api: ApiClient, session: SessionStore, bus: EventBus):
        super().__init__()
        self.config = config
        self.api = api
        self.session = session
        self.bus = bus
        self._workers = []
        self._system_health = {"backend": False, "voice": False, "llm": None}
        self._wake_word_active = False
        self._is_quitting = False
        self._reauth_in_progress = False

        self.setWindowTitle("OmniAssist V2")
        self.resize(1100, 740)

        self.state = AssistantState.IDLE

        # Main widgets
        self.conversation = ConversationView()
        self.orb = OrbVisualizer()
        self.timeline = ExecutionTimeline()

        # New Input Area
        self.input_container = QtWidgets.QFrame()
        self.input_container.setStyleSheet("""
            QFrame {
                background: #1f2630;
                border: 1px solid #374151;
                border-radius: 24px;
            }
        """)
        self.input_container.setFixedHeight(48)
        
        input_layout = QtWidgets.QHBoxLayout(self.input_container)
        input_layout.setContentsMargins(12, 0, 8, 0)
        input_layout.setSpacing(8)

        self.btn_attach = QtWidgets.QPushButton("📎")
        self.btn_attach.setFixedSize(42, 34)
        self.btn_attach.setStyleSheet("""
            QPushButton {
                background: #111827;
                color: #9ca3af;
                font-size: 16px;
                font-weight: 600;
                border: 1px solid #374151;
                border-radius: 17px;
                padding: 0;
            }
            QPushButton:hover {
                background: #1f2937;
                color: #e5e7eb;
            }
        """)
        self.btn_attach.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.btn_attach.setToolTip("Attach file")
        
        self.btn_voice = QtWidgets.QPushButton("🎤")
        self.btn_voice.setFixedSize(42, 34)
        self.btn_voice.setStyleSheet("""
            QPushButton {
                background: #111827;
                color: #9ca3af;
                font-size: 16px;
                font-weight: 600;
                border: 1px solid #374151;
                border-radius: 17px;
                padding: 0;
            }
            QPushButton:hover {
                background: #1f2937;
                color: #e5e7eb;
            }
        """)
        self.btn_voice.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.btn_voice.setToolTip("Start voice input")
        
        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("Ask OmniAssist anything...")
        self.input.setStyleSheet("background: transparent; color: white; border: none; font-size: 14px; font-family: 'Segoe UI', Arial;")
        
        # Command History setup
        self.history_filter = CommandHistoryFilter(self)
        self.input.installEventFilter(self.history_filter)
        
        self.btn_send = QtWidgets.QPushButton("➤")
        self.btn_send.setFixedSize(38, 38)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: #ffffff;
                border-radius: 19px;
                border: 1px solid #60a5fa;
                font-size: 15px;
                font-weight: 700;
                padding-left: 2px;
            }
            QPushButton:hover {
                background: #2563eb;
                border: 1px solid #93c5fd;
            }
            QPushButton:pressed {
                background: #1d4ed8;
                border: 1px solid #60a5fa;
            }
            QPushButton:disabled {
                background: #263244;
                color: #93a1b5;
                border: 1px solid #3a4a5f;
            }
        """)
        self.btn_send.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.btn_send.setToolTip("Send")
        self.btn_send.setEnabled(False)

        self._send_glow = QtWidgets.QGraphicsDropShadowEffect(self.btn_send)
        self._send_glow.setOffset(0, 0)
        self._send_glow.setBlurRadius(10)
        self._send_glow.setColor(QtGui.QColor(96, 165, 250, 70))
        self.btn_send.setGraphicsEffect(self._send_glow)

        self._send_pulse_anim = QtCore.QPropertyAnimation(self._send_glow, b"blurRadius", self)
        self._send_pulse_anim.setDuration(1300)
        self._send_pulse_anim.setStartValue(8)
        self._send_pulse_anim.setEndValue(22)
        self._send_pulse_anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutSine)
        self._send_pulse_anim.setLoopCount(-1)
        self._send_pulse_anim.start()
        
        self.btn_attach.clicked.connect(self._on_attach_file)
        self.btn_send.clicked.connect(self._on_send)
        self.btn_send.pressed.connect(self._animate_send_button_press)
        self.btn_send.released.connect(self._animate_send_button_release)
        self.input.returnPressed.connect(self._on_send)
        self.input.textChanged.connect(self._update_send_button_state)
        self.btn_voice.clicked.connect(self._toggle_listen)
        
        input_layout.addWidget(self.btn_attach)
        input_layout.addWidget(self.btn_voice)
        input_layout.addWidget(self.input, 1)
        input_layout.addWidget(self.btn_send)

        # Header Area (Identity, Controls, Orb)
        header_container = QtWidgets.QWidget()
        header_layout = QtWidgets.QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.setSpacing(10)
        
        # New Product-like Top Bar
        top_bar = QtWidgets.QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_title = QtWidgets.QLabel("OmniAssist")
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: 700; color: #e5e7eb; font-family: 'Segoe UI', sans-serif;")
        
        # Assistant State Label
        self.lbl_assistant_state = QtWidgets.QLabel("● Ready")
        self.lbl_assistant_state.setStyleSheet(""
            "color: #10b981;"
            "font-size: 13px;"
            "font-weight: 600;"
            "padding: 6px 12px;"
            "background: #172A22;"
            "border: 1px solid #1F6B4F;"
            "border-radius: 16px;"
            "font-family: 'Segoe UI', sans-serif;"
        "")
        self.lbl_assistant_state.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        
        # Settings Button
        self.btn_settings = QtWidgets.QPushButton("⚙ Settings")
        self.btn_settings.setFixedHeight(32)
        self.btn_settings.setMinimumWidth(104)
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background: #1f2937; color: #d1d5db; font-size: 13px; font-weight: 600; border-radius: 16px; padding: 0 12px;
            }
            QPushButton:hover {
                background: #374151; color: white;
            }
        """)
        self.btn_settings.clicked.connect(self._open_settings)

        self.btn_wake = QtWidgets.QPushButton("Wake Word: OFF")
        self.btn_wake.setFixedHeight(32)
        self.btn_wake.setMinimumWidth(130)
        self.btn_wake.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.btn_wake.clicked.connect(self._toggle_wake_word)
        self._update_wake_word_button(False)
        
        # Profile Button (icon-based user area entry)
        _username = "User"
        try:
            _user_data = session.user
            if isinstance(_user_data, dict):
                _username = _user_data.get("username") or _username
        except Exception:
            pass
        self.btn_profile = QtWidgets.QPushButton("")
        self.btn_profile.setFixedSize(36, 36)
        self.btn_profile.setIcon(self._build_user_icon())
        self.btn_profile.setIconSize(QtCore.QSize(16, 16))
        self.btn_profile.setStyleSheet("""
            QPushButton {
                background: #334155;
                color: #e5e7eb;
                border-radius: 18px;
                border: 1px solid #64748b;
            }
            QPushButton:hover {
                background: #3f4f66;
                border: 1px solid #93a4bc;
            }
        """)
        self.btn_profile.setToolTip(f"User area: {_username} | Personalization")
        self.btn_profile.setAccessibleName("User Area")
        self.btn_profile.clicked.connect(self._open_profile)

        self._profile_glow = QtWidgets.QGraphicsDropShadowEffect(self.btn_profile)
        self._profile_glow.setOffset(0, 0)
        self._profile_glow.setColor(QtGui.QColor(96, 165, 250, 120))
        self._profile_glow.setBlurRadius(10)
        self.btn_profile.setGraphicsEffect(self._profile_glow)

        self._profile_glow_anim = QtCore.QPropertyAnimation(self._profile_glow, b"blurRadius", self)
        self._profile_glow_anim.setDuration(1700)
        self._profile_glow_anim.setStartValue(8)
        self._profile_glow_anim.setEndValue(22)
        self._profile_glow_anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutSine)
        self._profile_glow_anim.setLoopCount(-1)
        self._profile_glow_anim.start()
        
        top_bar.addWidget(self.lbl_title)
        top_bar.addStretch()
        top_bar.addWidget(self.lbl_assistant_state)
        top_bar.addSpacing(12)
        top_bar.addWidget(self.btn_wake)
        top_bar.addSpacing(8)
        top_bar.addWidget(self.btn_settings)
        top_bar.addSpacing(8)
        top_bar.addWidget(self.btn_profile)
        
        header_layout.addLayout(top_bar)
        
        # Orb Area
        orb_row = QtWidgets.QHBoxLayout()
        orb_row.addStretch()
        orb_row.addWidget(self.orb)
        orb_row.addStretch()
        header_layout.addLayout(orb_row)

        self.lbl_orb_state = QtWidgets.QLabel("Ready")
        self.lbl_orb_state.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.lbl_orb_state.setStyleSheet(
            "color: #9ca3af; font-size: 13px; font-weight: 600; margin-top: 2px; margin-bottom: 4px;"
        )
        header_layout.addWidget(self.lbl_orb_state)
        
        # Audio Waveform (hidden by default)
        waveform_row = QtWidgets.QHBoxLayout()
        self.waveform = WaveformWidget()
        self.waveform.hide()
        waveform_row.addStretch()
        waveform_row.addWidget(self.waveform)
        waveform_row.addStretch()
        header_layout.addLayout(waveform_row)

        # Add soft shadow
        shadow = QtWidgets.QGraphicsDropShadowEffect(self.input_container)
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.input_container.setGraphicsEffect(shadow)
        
        # Layout
        central = QtWidgets.QWidget()
        central.setStyleSheet("background-color: #0f1117;")

        self.particle_field = ParticleField(central, particle_count=28)
        self.particle_field.setGeometry(0, 0, central.width(), central.height())
        self.particle_field.lower()

        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        root.addWidget(header_container, 0)

        # Chat and Activity container
        self.conversation.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        root.addWidget(self.conversation, 1)

        # Timeline has fixed maximum height to not take over chat
        self.timeline.setMaximumHeight(180)
        root.addWidget(self.timeline, 0)

        # Contains everything inside one container now
        root.addWidget(self.input_container, 0)

        self.setCentralWidget(central)

        # Tray notifications (Windows)
        self._tray = QtWidgets.QSystemTrayIcon(self)
        icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon)
        self._tray.setIcon(icon)
        self._tray.setToolTip("OmniAssist")
        self._tray.setVisible(True)
        self._setup_tray_mode()

        # Socket client
        self.socket = SocketClient(socket_url=config.socket_url, session=session, bus=bus)
        self.socket.connect()

        # Event wiring
        self.bus.connection_status.connect(self._on_connection_status)
        self.bus.status_changed.connect(self._on_status_changed)
        self.bus.execution_step.connect(self._on_execution_step)
        self.bus.command_result.connect(self._on_command_result)
        self.bus.error.connect(self._on_error)
        self.bus.confirmation_required.connect(self._on_confirmation_required)
        self.bus.confirmation_result.connect(self._on_confirmation_result)
        self.bus.listening_status.connect(self._on_listening_status)
        self.bus.voice_input.connect(self._on_voice_input)
        self.bus.wake_word_status.connect(self._on_wake_word_status)
        self.bus.wake_word_detected.connect(self._on_wake_word_detected)
        self.conversation.suggestions.suggestion_clicked.connect(self._on_suggestion_clicked)

        # Initial health checks (best-effort)
        ok, health = self.api.health()
        self._refresh_wake_word_status()

        self._set_state(AssistantState.IDLE)

    @QtCore.Slot(str)
    def _update_send_button_state(self, text: str) -> None:
        has_text = bool((text or "").strip())
        self.btn_send.setEnabled(has_text)
        if has_text:
            self._send_glow.setColor(QtGui.QColor(96, 165, 250, 170))
        else:
            self._send_glow.setColor(QtGui.QColor(96, 165, 250, 70))

    @QtCore.Slot()
    def _animate_send_button_press(self) -> None:
        if not self.btn_send.isEnabled():
            return
        self._send_click_anim = QtCore.QPropertyAnimation(self._send_glow, b"blurRadius", self)
        self._send_click_anim.setDuration(90)
        self._send_click_anim.setStartValue(float(self._send_glow.blurRadius()))
        self._send_click_anim.setEndValue(7.0)
        self._send_click_anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutQuad)
        self._send_click_anim.start()

    @QtCore.Slot()
    def _animate_send_button_release(self) -> None:
        if not self.btn_send.isEnabled():
            return
        self._send_release_anim = QtCore.QPropertyAnimation(self._send_glow, b"blurRadius", self)
        self._send_release_anim.setDuration(160)
        self._send_release_anim.setStartValue(float(self._send_glow.blurRadius()))
        self._send_release_anim.setEndValue(18.0)
        self._send_release_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self._send_release_anim.start()

    def _notify_user(self, message: str, *, force_status: str | None = None) -> None:
        """Show user-facing tray notifications with smarter severity + wording."""
        msg = (message or "").strip()
        if not msg:
            return

        lower = msg.lower()
        status = force_status or "info"

        if force_status is None:
            if any(k in lower for k in ["error", "failed", "cannot", "could not"]):
                status = "error"
            elif any(k in lower for k in ["auth", "authentication", "smtp", "password", "not configured"]):
                status = "warning"
            elif any(k in lower for k in ["sent", "success", "completed", "done"]):
                status = "success"

        icon = QtWidgets.QSystemTrayIcon.MessageIcon.Information
        title = "OmniAssist"
        display_message = msg

        if "email sent" in lower or ("sent" in lower and "email" in lower):
            title = "Email"
            display_message = "✔ Email sent successfully"
            status = "success"
        elif any(k in lower for k in ["gmail", "smtp", "authentication failed", "app password", "not configured"]):
            title = "Email Setup"
            display_message = "⚠ Gmail authentication needed"
            status = "warning"

        if status == "error":
            icon = QtWidgets.QSystemTrayIcon.MessageIcon.Critical
        elif status == "warning":
            icon = QtWidgets.QSystemTrayIcon.MessageIcon.Warning
        else:
            icon = QtWidgets.QSystemTrayIcon.MessageIcon.Information

        self._tray.showMessage(title, display_message, icon, 4000)

    def _build_user_icon(self) -> QtGui.QIcon:
        """Create a small vector avatar icon to avoid emoji font fallback issues."""
        size = 24
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor("#dbeafe"))
        painter.drawEllipse(QtCore.QRectF(8.0, 4.0, 8.0, 8.0))

        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(5.0, 12.0, 14.0, 8.0), 4.0, 4.0)
        painter.drawPath(path)

        painter.end()
        return QtGui.QIcon(pixmap)

    def _setup_tray_mode(self) -> None:
        """Configure system tray interactions and context menu."""
        tray_menu = QtWidgets.QMenu()
        tray_menu.setStyleSheet(
            """
            QMenu {
                background: #161b22;
                color: #e5e7eb;
                border: 1px solid #2b3441;
                border-radius: 10px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 14px;
                border-radius: 8px;
                margin: 2px 0;
            }
            QMenu::item:selected {
                background: #1f2937;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #2b3441;
                margin: 6px 2px;
            }
            """
        )

        self.act_open = tray_menu.addAction("Open OmniAssist")
        self.act_open.triggered.connect(self._restore_from_tray)

        self.act_voice_mode = tray_menu.addAction("Voice Mode")
        self.act_voice_mode.setCheckable(True)
        self.act_voice_mode.triggered.connect(self._toggle_voice_mode_from_tray)

        tray_menu.addSeparator()

        self.act_quit = tray_menu.addAction("Quit")
        self.act_quit.triggered.connect(self._quit_from_tray)

        self._tray.setContextMenu(tray_menu)
        self._tray.activated.connect(self._on_tray_activated)

    def _restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _toggle_voice_mode_from_tray(self, checked: bool):
        listening = self.state == AssistantState.LISTENING
        if checked != listening:
            self._toggle_listen()

    def _quit_from_tray(self):
        self._is_quitting = True
        self.close()

    def _shutdown_cleanup(self):
        """Best-effort cleanup when app is truly exiting."""
        try:
            self.orb.animation.stop()
        except Exception:
            pass

        for w in list(self._workers):
            try:
                w.wait(50)
            except Exception:
                pass
        self._workers.clear()

        try:
            self.socket.disconnect()
        except Exception:
            pass

        try:
            self._tray.hide()
        except Exception:
            pass

    def _set_state(self, new_state: AssistantState) -> None:
        processing_states = {
            AssistantState.THINKING,
            AssistantState.EXECUTING,
            AssistantState.RESPONDING,
            AssistantState.WAITING_CONFIRMATION,
        }

        if new_state in processing_states:
            self.conversation.show_thinking()
        elif self.state in processing_states and new_state not in processing_states:
            self.conversation.hide_thinking()
            
        if new_state == AssistantState.LISTENING:
            self.waveform.start()
        elif self.state == AssistantState.LISTENING and new_state != AssistantState.LISTENING:
            self.waveform.stop()
            
        self.state = new_state
        self.orb.set_state(new_state.value)
        
        # Update text description
        state_map = {
            AssistantState.IDLE: ("● Ready", "#10b981", "#172A22", "#1F6B4F"),
            AssistantState.LISTENING: ("● Listening", "#ef4444", "#2A1717", "#7F1D1D"),
            AssistantState.THINKING: ("● Thinking", "#60a5fa", "#152238", "#1E40AF"),
            AssistantState.EXECUTING: ("● Executing", "#60a5fa", "#152238", "#1E40AF"),
            AssistantState.RESPONDING: ("● Speaking", "#60a5fa", "#152238", "#1E40AF"),
            AssistantState.ERROR: ("● Error", "#f59e0b", "#2D220F", "#92400E"),
            AssistantState.WAITING_CONFIRMATION: ("● Awaiting confirmation", "#f59e0b", "#2D220F", "#92400E"),
        }
        state_text, state_color, badge_bg, badge_border = state_map.get(
            new_state,
            ("● Ready", "#10b981", "#172A22", "#1F6B4F"),
        )
        self.lbl_orb_state.setText(state_text.replace("● ", ""))
        
        # Voice button states: Idle=🎤, Listening=🔴, Processing=⏳
        if new_state == AssistantState.LISTENING:
            self.btn_voice.setText("🔴")
            self.btn_voice.setStyleSheet("""
                QPushButton {
                    background: #2A1717;
                    color: #ef4444;
                    font-size: 16px;
                    font-weight: 700;
                    border: 1px solid #7F1D1D;
                    border-radius: 17px;
                    padding: 0;
                }
                QPushButton:hover {
                    background: #3A1E1E;
                    color: #f87171;
                }
            """)
            self.btn_voice.setToolTip("Listening")
        elif new_state in processing_states:
            self.btn_voice.setText("⏳")
            self.btn_voice.setStyleSheet("""
                QPushButton {
                    background: #2A220F;
                    color: #fbbf24;
                    font-size: 16px;
                    font-weight: 700;
                    border: 1px solid #92400E;
                    border-radius: 17px;
                    padding: 0;
                }
                QPushButton:hover {
                    background: #3A2B10;
                    color: #fcd34d;
                }
            """)
            self.btn_voice.setToolTip("Processing")
        else:
            self.btn_voice.setText("🎤")
            self.btn_voice.setStyleSheet("""
                QPushButton {
                    background: #111827;
                    color: #9ca3af;
                    font-size: 16px;
                    font-weight: 600;
                    border: 1px solid #374151;
                    border-radius: 17px;
                    padding: 0;
                }
                QPushButton:hover {
                    background: #1f2937;
                    color: #e5e7eb;
                }
            """)
            self.btn_voice.setToolTip("Start voice input")

        self.lbl_assistant_state.setStyleSheet(
            ""
            f"color: {state_color};"
            "font-size: 13px;"
            "font-weight: 600;"
            "padding: 6px 12px;"
            f"background: {badge_bg};"
            f"border: 1px solid {badge_border};"
            "border-radius: 16px;"
            "font-family: 'Segoe UI', sans-serif;"
            ""
        )
        self.lbl_assistant_state.setText(state_text)

        if hasattr(self, "act_voice_mode"):
            self.act_voice_mode.setChecked(new_state == AssistantState.LISTENING)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if not self._is_quitting and self._tray.isVisible():
            self.hide()
            self._tray.showMessage(
                "OmniAssist",
                "Minimized to system tray. Right-click the tray icon for options.",
                QtWidgets.QSystemTrayIcon.MessageIcon.Information,
                2200,
            )
            event.ignore()
            return

        self._shutdown_cleanup()
        event.accept()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        if hasattr(self, "particle_field") and self.centralWidget() is not None:
            self.particle_field.setGeometry(self.centralWidget().rect())

    @QtCore.Slot()
    def _on_send(self):
        text = self.input.text().strip()
        if not text:
            return

        self.timeline.clear()
        self.timeline.add_action_note("Parsed command", [text], status="done")
        recipient = self._extract_recipient(text)
        if recipient:
            self.timeline.add_action_note("Extracted recipient", [f"Recipient: {recipient}"], status="done")

        self.history_filter.add(text)
        self.conversation.add_user(text)
        self.input.clear()
        self._set_state(AssistantState.THINKING)

        # Run in background thread to avoid UI freeze
        worker = _CommandWorker(self.api, text)
        worker.result.connect(self._on_rest_result)
        self._workers.append(worker)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        worker.start()

    @QtCore.Slot(str)
    def _on_suggestion_clicked(self, text: str):
        self.input.setText(text)
        self.input.setFocus()

    @QtCore.Slot()
    def _on_attach_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Attach file",
            "",
            "All Files (*.*)",
        )
        if not file_path:
            return

        current = self.input.text().strip()
        attach_text = f'attach file "{file_path}"'
        if current:
            self.input.setText(f"{current} {attach_text}")
        else:
            self.input.setText(attach_text)
        self.input.setFocus()

    def _extract_recipient(self, command: str) -> str:
        """Best-effort recipient extraction for user-facing step feedback."""
        text = (command or "").strip()
        if not text:
            return ""

        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        if email_match:
            return email_match.group(0)

        to_match = re.search(r"\bto\s+([A-Za-z0-9._%+-]+)\b", text, flags=re.IGNORECASE)
        if to_match:
            return to_match.group(1)

        return ""

    def _cleanup_worker(self, worker) -> None:
        if worker in self._workers:
            self._workers.remove(worker)

    @QtCore.Slot(dict)
    def _on_rest_result(self, payload: dict):
        # REST response is redundant with socket command_result, but acts as fallback.
        status = payload.get("status")
        code = str(payload.get("code") or "").lower()
        msg = str(payload.get("message") or "")

        if code == "unauthorized":
            self._handle_unauthorized(msg or "Session expired. Please sign in again.")
            return

        if status == "confirmation_required":
            self._set_state(AssistantState.WAITING_CONFIRMATION)
        elif status == "error":
            self._set_state(AssistantState.ERROR)
            if msg:
                self.conversation.add_system(f"Error: {msg}")
                self._notify_user(msg, force_status="error")
        else:
            self._set_state(AssistantState.RESPONDING)

    @QtCore.Slot(dict)
    def _on_connection_status(self, data: dict):
        payload = data or {}
        self._system_health["backend"] = bool(payload.get("status") in ["connected", "ok"] or payload.get("connected"))
        self._system_health["voice"] = bool(payload.get("listening"))
        self._system_health["llm"] = payload.get("llm")
        if "wake_word_active" in payload:
            self._update_wake_word_button(bool(payload.get("wake_word_active")))
        self.lbl_assistant_state.setToolTip(
            f"backend={self._system_health['backend']}, "
            f"voice={self._system_health['voice']}, "
            f"llm={self._system_health['llm']}"
        )

    @QtCore.Slot(dict)
    def _on_status_changed(self, data: dict):
        pass

    @QtCore.Slot(dict)
    def _on_execution_step(self, data: dict):
        # Current backend emits only "running" (plan steps). We'll update this once backend streams finish/fail.
        self._set_state(AssistantState.EXECUTING)
        self.timeline.upsert_step(data)

    @QtCore.Slot(dict)
    def _on_command_result(self, data: dict):
        message = (data or {}).get("message") or ""
        if message:
            self.conversation.add_assistant(self._personalize_assistant_message(message))

        # Show what planned the action (ollama vs fallback), when available.
        meta = (data or {}).get("meta")
        plan_source = None
        if isinstance(meta, dict):
            trace = meta.get("loop_trace")
            if isinstance(trace, list) and trace:
                first = trace[0] if isinstance(trace[0], dict) else {}
                plan_source = first.get("plan_source")

        self._set_state(AssistantState.RESPONDING)
        self._notify_user(message or "Task completed.")
        QtCore.QTimer.singleShot(700, lambda: self._set_state(AssistantState.IDLE))

    @QtCore.Slot(dict)
    def _on_error(self, data: dict):
        msg = (data or {}).get("message") or str(data)
        code = str((data or {}).get("code") or "").lower()
        if code == "unauthorized":
            self._handle_unauthorized(msg or "Session expired. Please sign in again.")
            return
        self.conversation.add_system(f"Error: {msg}")
        self._set_state(AssistantState.ERROR)
        self._notify_user(msg, force_status="error")

    def _handle_unauthorized(self, message: str) -> None:
        if self._reauth_in_progress:
            return

        self._reauth_in_progress = True
        try:
            try:
                self.socket.disconnect()
            except Exception:
                pass

            if hasattr(self.session, "clear"):
                self.session.clear()

            self.conversation.add_system(message)
            self._notify_user(message, force_status="warning")
            self._set_state(AssistantState.ERROR)

            dlg = LoginDialog(api=self.api, parent=self)
            if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                self.socket.connect()
                self._set_state(AssistantState.IDLE)
                self.conversation.add_assistant("Session restored. You can continue.")
            else:
                self.close()
        finally:
            self._reauth_in_progress = False

    @QtCore.Slot(dict)
    def _on_confirmation_required(self, data: dict):
        self._set_state(AssistantState.WAITING_CONFIRMATION)
        message = (data or {}).get("message", "Confirm action?")
        self.conversation.add_assistant(message)
        self.timeline.add_action_note(
            "Waiting confirmation",
            [message],
            status="pending",
        )
        card_data = self._extract_email_card_data(message)
        if card_data is not None:
            self.conversation.add_email_command_card(
                recipient=card_data["recipient"],
                subject=card_data["subject"],
                body=card_data["body"],
                on_send=self._submit_confirmation_from_card,
                on_edit=self._edit_confirmation_from_card,
            )
            return

        self.conversation.add_confirmation_prompt(message, self._submit_confirmation)

    def _extract_email_card_data(self, message: str) -> dict | None:
        text = (message or "").strip()
        lower = text.lower()
        if "email" not in lower:
            return None

        recipient_match = re.search(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", text)
        subject_match = re.search(r"subject\s*[:=]\s*['\"]?([^'\"\n]+)", text, flags=re.IGNORECASE)
        body_match = re.search(r"body\s*[:=]\s*['\"]?([^'\"\n]+)", text, flags=re.IGNORECASE)

        return {
            "recipient": recipient_match.group(1) if recipient_match else "",
            "subject": (subject_match.group(1).strip() if subject_match else "-"),
            "body": (body_match.group(1).strip() if body_match else "hello"),
        }

    @QtCore.Slot(dict)
    def _submit_confirmation_from_card(self, payload: dict):
        self._submit_confirmation(True)

    @QtCore.Slot(dict)
    def _edit_confirmation_from_card(self, payload: dict):
        recipient = (payload or {}).get("recipient", "")
        subject = (payload or {}).get("subject", "")
        body = (payload or {}).get("body", "")

        edit_cmd = (
            f'send email to {recipient} '
            f'subject "{subject or "-"}" '
            f'body "{body or "hello"}"'
        ).strip()
        self.input.setText(edit_cmd)
        self.input.setFocus()
        self.timeline.add_action_note("Edit requested", ["Updated command is ready in input box."], status="running")
        self._submit_confirmation(False)

    def _submit_confirmation(self, approved: bool):
        # Send confirmation in background to avoid blocking the UI.
        worker = _ConfirmWorker(self.api, approved=approved)
        worker.result.connect(self._on_confirm_rest_result)
        self._workers.append(worker)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        worker.start()

    def _open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()
        if dlg.signout_requested:
            if hasattr(self.session, 'clear'):
                self.session.clear()
            self.close()

    def _open_profile(self):
        dlg = ProfileDialog(self.api, self.session, self)
        dlg.exec()

    def _update_wake_word_button(self, active: bool) -> None:
        self._wake_word_active = bool(active)
        if self._wake_word_active:
            self.btn_wake.setText("Wake Word: ON")
            self.btn_wake.setToolTip("Wake-word detector is active")
            self.btn_wake.setStyleSheet(
                """
                QPushButton {
                    background: #163321;
                    color: #86efac;
                    font-size: 13px;
                    font-weight: 700;
                    border-radius: 16px;
                    border: 1px solid #22c55e;
                    padding: 0 12px;
                }
                QPushButton:hover {
                    background: #1a472b;
                    color: #bbf7d0;
                }
                """
            )
        else:
            self.btn_wake.setText("Wake Word: OFF")
            self.btn_wake.setToolTip("Click to activate wake-word detector")
            self.btn_wake.setStyleSheet(
                """
                QPushButton {
                    background: #2f2430;
                    color: #fda4af;
                    font-size: 13px;
                    font-weight: 700;
                    border-radius: 16px;
                    border: 1px solid #ef4444;
                    padding: 0 12px;
                }
                QPushButton:hover {
                    background: #3b2a3c;
                    color: #fecdd3;
                }
                """
            )

    def _refresh_wake_word_status(self) -> None:
        worker = _WakeWordStatusWorker(self.api)
        worker.result.connect(self._on_wake_word_status_result)
        self._workers.append(worker)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        worker.start()

    @QtCore.Slot(dict)
    def _on_wake_word_status_result(self, payload: dict) -> None:
        active = bool((payload or {}).get("active"))
        self._update_wake_word_button(active)

    def _personalize_assistant_message(self, message: str) -> str:
        username = ""
        try:
            user = self.session.user or {}
            username = str(user.get("username") or "").strip()
        except Exception:
            username = ""

        if not username or not message:
            return message

        lowered = message.lower().strip()
        if username.lower() in lowered:
            return message

        if lowered.startswith("sure"):
            return f"Sure {username}, {message[5:].lstrip()}"

        if lowered.startswith("i will") or lowered.startswith("i'll"):
            return f"Sure {username}, {message}"

        return message

    def _on_tray_activated(self, reason):
        if reason in (
            QtWidgets.QSystemTrayIcon.ActivationReason.Trigger,
            QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._restore_from_tray()

    @QtCore.Slot(dict)
    def _on_confirm_rest_result(self, payload: dict):
        # Socket event `confirmation_result` is the canonical signal; REST response is fallback.
        status = payload.get("status")
        msg = payload.get("message")
        if msg:
            if status == "success":
                self.conversation.add_assistant(msg)
            else:
                self.conversation.add_system(msg)

    @QtCore.Slot(dict)
    def _on_confirmation_result(self, data: dict):
        msg = (data or {}).get("message") or ""
        status = (data or {}).get("status") or ""
        if msg:
            if status == "success":
                self.conversation.add_assistant(self._personalize_assistant_message(msg))
                self._notify_user(msg, force_status="success")
            else:
                self.conversation.add_system(msg)
                self._notify_user(msg, force_status="warning")
        self._set_state(AssistantState.IDLE)

    @QtCore.Slot(dict)
    def _on_listening_status(self, data: dict):
        listening = bool((data or {}).get("listening"))
        self._set_state(AssistantState.LISTENING if listening else AssistantState.IDLE)

    @QtCore.Slot(dict)
    def _on_voice_input(self, data: dict):
        # Show transcript as system message for now.
        text = (data or {}).get("text")
        if text:
            self.conversation.add_system(f"Heard: {text}")

    @QtCore.Slot(dict)
    def _on_wake_word_status(self, data: dict):
        self._update_wake_word_button(bool((data or {}).get("active")))

    @QtCore.Slot(dict)
    def _on_wake_word_detected(self, data: dict):
        word = str((data or {}).get("word") or "wake word")
        self.conversation.add_system(f"Wake word detected: {word}")

    @QtCore.Slot()
    def _toggle_listen(self):
        self.btn_voice.setEnabled(False)
        worker = _ListenToggleWorker(self.api)
        worker.result.connect(self._on_listen_toggled)
        self._workers.append(worker)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        worker.start()

    @QtCore.Slot(dict)
    def _on_listen_toggled(self, payload: dict):
        self.btn_voice.setEnabled(True)
        ok = bool((payload or {}).get("ok"))
        if not ok:
            message = str((payload or {}).get("message") or "Unable to toggle listening right now")
            self.conversation.add_system(f"Error: {message}")
            self._notify_user(message, force_status="warning")

    @QtCore.Slot()
    def _toggle_wake_word(self):
        self.btn_wake.setEnabled(False)
        worker = _WakeWordToggleWorker(self.api, should_start=not self._wake_word_active)
        worker.result.connect(self._on_wake_word_toggled)
        self._workers.append(worker)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        worker.start()

    @QtCore.Slot(dict)
    def _on_wake_word_toggled(self, payload: dict):
        self.btn_wake.setEnabled(True)
        active = bool((payload or {}).get("active"))
        ok = bool((payload or {}).get("ok"))

        if ok:
            self._update_wake_word_button(active)
            state_text = "enabled" if active else "disabled"
            self.conversation.add_system(f"Wake word {state_text}.")
        else:
            message = str((payload or {}).get("message") or "Failed to toggle wake word")
            self.conversation.add_system(f"Error: {message}")
            self._notify_user(message, force_status="warning")
            self._refresh_wake_word_status()


class _CommandWorker(QtCore.QThread):
    result = QtCore.Signal(dict)

    def __init__(self, api: ApiClient, command: str):
        super().__init__()
        self.api = api
        self.command = command

    def run(self):
        try:
            resp = self.api.process_command(self.command)
            try:
                payload = resp.json() if resp.content else {}
            except Exception:
                payload = {}

            if resp.status_code == 401:
                try:
                    self.api.session.clear()
                except Exception:
                    pass
                self.result.emit({
                    "status": "error",
                    "code": "unauthorized",
                    "message": (payload.get("message") if isinstance(payload, dict) else "") or "Session expired. Please sign in again.",
                })
                return

            if resp.status_code >= 400:
                err_msg = (payload.get("message") if isinstance(payload, dict) else "") or f"Command failed with HTTP {resp.status_code}"
                self.result.emit({"status": "error", "message": err_msg})
                return

            self.result.emit(payload if isinstance(payload, dict) else {"status": "success", "message": str(payload)})
        except Exception as exc:
            self.result.emit({"status": "error", "message": str(exc)})


class _ConfirmWorker(QtCore.QThread):
    result = QtCore.Signal(dict)

    def __init__(self, api: ApiClient, approved: bool):
        super().__init__()
        self.api = api
        self.approved = approved

    def run(self):
        try:
            res = self.api.send_confirmation(self.approved)
            payload = res.data if isinstance(res.data, dict) else {"status": "success" if res.ok else "error", "message": res.message}
            self.result.emit(payload)
        except Exception as exc:
            self.result.emit({"status": "error", "message": str(exc)})


class _WakeWordStatusWorker(QtCore.QThread):
    result = QtCore.Signal(dict)

    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api

    def run(self):
        try:
            ok, data = self.api.wake_word_status()
            payload = data if isinstance(data, dict) else {}
            payload["ok"] = ok
            self.result.emit(payload)
        except Exception as exc:
            self.result.emit({"ok": False, "active": False, "message": str(exc)})


class _WakeWordToggleWorker(QtCore.QThread):
    result = QtCore.Signal(dict)

    def __init__(self, api: ApiClient, should_start: bool):
        super().__init__()
        self.api = api
        self.should_start = should_start

    def run(self):
        try:
            ok = self.api.wake_word_start() if self.should_start else self.api.wake_word_stop()
            status_ok, status = self.api.wake_word_status()
            payload = status if isinstance(status, dict) else {}
            payload["ok"] = bool(ok and status_ok)
            if not payload["ok"] and not payload.get("message"):
                payload["message"] = "Wake-word request was not accepted by backend"
            self.result.emit(payload)
        except Exception as exc:
            self.result.emit({"ok": False, "active": False, "message": str(exc)})


class _ListenToggleWorker(QtCore.QThread):
    result = QtCore.Signal(dict)

    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api

    def run(self):
        try:
            ok, status = self.api.get_status()
            listening = bool(status.get("listening")) if ok and isinstance(status, dict) else False
            toggle_ok = self.api.stop_listening() if listening else self.api.start_listening()
            self.result.emit({"ok": bool(toggle_ok)})
        except Exception as exc:
            self.result.emit({"ok": False, "message": str(exc)})
