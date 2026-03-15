from __future__ import annotations

from PySide6 import QtWidgets


class StatusIndicator(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._api = QtWidgets.QLabel("API: ?")
        self._socket = QtWidgets.QLabel("Socket: ?")
        self._state = QtWidgets.QLabel("State: IDLE")
        self._llm = QtWidgets.QLabel("LLM: ?")
        self._listening = QtWidgets.QLabel("Listening: no")
        self._confirm = QtWidgets.QLabel("Confirm: no")

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self._api)
        layout.addWidget(self._socket)
        layout.addWidget(self._state)
        layout.addWidget(self._llm)
        layout.addStretch(1)
        layout.addWidget(self._listening)
        layout.addWidget(self._confirm)

    def set_api_ok(self, ok: bool, status: str | None = None) -> None:
        self._api.setText(f"API: {'✓' if ok else '✗'}{'' if not status else ' ' + str(status)}")

    def set_socket_connected(self, connected: bool) -> None:
        self._socket.setText(f"Socket: {'✓' if connected else '✗'}")

    def set_state(self, state: str) -> None:
        self._state.setText(f"State: {state}")

    def set_llm_source(self, source: str | None) -> None:
        if not source:
            self._llm.setText("LLM: ?")
            return
        self._llm.setText(f"LLM: {source}")

    def set_listening(self, listening: bool) -> None:
        self._listening.setText(f"Listening: {'yes' if listening else 'no'}")

    def set_confirmation_pending(self, pending: bool) -> None:
        self._confirm.setText(f"Confirm: {'yes' if pending else 'no'}")
