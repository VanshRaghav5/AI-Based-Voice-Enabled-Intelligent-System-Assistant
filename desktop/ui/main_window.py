from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from desktop.config import DesktopConfig
from desktop.core.assistant_state import AssistantState
from desktop.core.event_bus import EventBus
from desktop.services.api_client import ApiClient
from desktop.services.session_store import SessionStore
from desktop.services.socket_client import SocketClient
from desktop.ui.conversation_view import ConversationView
from desktop.ui.execution_timeline import ExecutionTimeline
from desktop.ui.orb_visualizer import OrbVisualizer
from desktop.ui.status_indicator import StatusIndicator


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, config: DesktopConfig, api: ApiClient, session: SessionStore, bus: EventBus):
        super().__init__()
        self.config = config
        self.api = api
        self.session = session
        self.bus = bus

        self.setWindowTitle("OmniAssist V2")
        self.resize(1100, 740)

        self.state = AssistantState.IDLE

        # Top status bar
        self.status_indicator = StatusIndicator()

        # Main widgets
        self.conversation = ConversationView()
        self.orb = OrbVisualizer()
        self.timeline = ExecutionTimeline()

        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("Type a command…")
        self.btn_send = QtWidgets.QPushButton("Send")
        self.btn_voice = QtWidgets.QPushButton("Listen")

        self.btn_send.clicked.connect(self._on_send)
        self.input.returnPressed.connect(self._on_send)
        self.btn_voice.clicked.connect(self._toggle_listen)

        # Layout
        central = QtWidgets.QWidget()
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)
        root.addWidget(self.status_indicator)

        content = QtWidgets.QVBoxLayout()

        content.addWidget(self.conversation, 1)

        lower = QtWidgets.QHBoxLayout()
        lower.addWidget(self.orb, 0)
        lower.addWidget(self.timeline, 1)
        content.addLayout(lower)

        input_row = QtWidgets.QHBoxLayout()
        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.btn_voice)
        input_row.addWidget(self.btn_send)
        content.addLayout(input_row)

        root.addLayout(content, 1)
        self.setCentralWidget(central)

        # Socket client
        self.socket = SocketClient(socket_url=config.socket_url, session=session, bus=bus)
        self.socket.connect()

        # Event wiring
        self.bus.connection_status.connect(self._on_connection_status)
        self.bus.execution_step.connect(self._on_execution_step)
        self.bus.command_result.connect(self._on_command_result)
        self.bus.error.connect(self._on_error)
        self.bus.confirmation_required.connect(self._on_confirmation_required)
        self.bus.listening_status.connect(self._on_listening_status)
        self.bus.voice_input.connect(self._on_voice_input)

        self.conversation.add_system("Connected to backend UI shell (V2).")

        # Initial health checks (best-effort)
        ok, health = self.api.health()
        self.status_indicator.set_api_ok(ok, health.get("status") if isinstance(health, dict) else None)

        self._set_state(AssistantState.IDLE)

    def _set_state(self, new_state: AssistantState) -> None:
        self.state = new_state
        self.status_indicator.set_state(new_state.value)
        self.orb.set_state(new_state.value)

    @QtCore.Slot()
    def _on_send(self):
        text = self.input.text().strip()
        if not text:
            return

        self.conversation.add_user(text)
        self.input.clear()
        self._set_state(AssistantState.THINKING)

        # Run in background thread to avoid UI freeze
        worker = _CommandWorker(self.api, text)
        worker.result.connect(self._on_rest_result)
        worker.start()

    @QtCore.Slot(dict)
    def _on_rest_result(self, payload: dict):
        # REST response is redundant with socket command_result, but acts as fallback.
        status = payload.get("status")
        if status == "confirmation_required":
            self._set_state(AssistantState.WAITING_CONFIRMATION)
        elif status == "error":
            self._set_state(AssistantState.ERROR)
        else:
            self._set_state(AssistantState.RESPONDING)

    @QtCore.Slot(dict)
    def _on_connection_status(self, data: dict):
        self.status_indicator.set_socket_connected(True)
        if isinstance(data, dict):
            self.status_indicator.set_listening(bool(data.get("listening")))
            self.status_indicator.set_confirmation_pending(bool(data.get("pending_confirmation")))

    @QtCore.Slot(dict)
    def _on_execution_step(self, data: dict):
        # Current backend emits only "running" (plan steps). We'll update this once backend streams finish/fail.
        self._set_state(AssistantState.EXECUTING)
        self.timeline.upsert_step(data)

    @QtCore.Slot(dict)
    def _on_command_result(self, data: dict):
        message = (data or {}).get("message") or ""
        if message:
            self.conversation.add_assistant(message)
        self._set_state(AssistantState.IDLE)

    @QtCore.Slot(dict)
    def _on_error(self, data: dict):
        msg = (data or {}).get("message") or str(data)
        self.conversation.add_system(f"Error: {msg}")
        self._set_state(AssistantState.ERROR)

    @QtCore.Slot(dict)
    def _on_confirmation_required(self, data: dict):
        self._set_state(AssistantState.WAITING_CONFIRMATION)
        message = (data or {}).get("message", "Confirm action?")
        self.conversation.add_system(f"Confirmation required: {message}")

    @QtCore.Slot(dict)
    def _on_listening_status(self, data: dict):
        listening = bool((data or {}).get("listening"))
        self.status_indicator.set_listening(listening)
        self._set_state(AssistantState.LISTENING if listening else AssistantState.IDLE)

    @QtCore.Slot(dict)
    def _on_voice_input(self, data: dict):
        # Show transcript as system message for now.
        text = (data or {}).get("text")
        if text:
            self.conversation.add_system(f"Heard: {text}")

    @QtCore.Slot()
    def _toggle_listen(self):
        # Toggle via REST; backend will emit listening_status.
        ok, status = self.api.get_status()
        listening = bool(status.get("listening")) if ok and isinstance(status, dict) else False
        if listening:
            self.api.stop_listening()
        else:
            self.api.start_listening()


class _CommandWorker(QtCore.QThread):
    result = QtCore.Signal(dict)

    def __init__(self, api: ApiClient, command: str):
        super().__init__()
        self.api = api
        self.command = command

    def run(self):
        try:
            resp = self.api.process_command(self.command)
            payload = resp.json() if resp.content else {}
            self.result.emit(payload if isinstance(payload, dict) else {"status": "success", "message": str(payload)})
        except Exception as exc:
            self.result.emit({"status": "error", "message": str(exc)})
