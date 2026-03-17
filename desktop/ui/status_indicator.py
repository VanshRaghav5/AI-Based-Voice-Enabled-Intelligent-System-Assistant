from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class StatusIndicator(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._status_badge = QtWidgets.QLabel("● Ready")
        self._status_badge.setStyleSheet(
            "color: #10b981; font-size: 13px; font-weight: 600; "
            "padding: 6px 12px; background: #172A22; border: 1px solid #1F6B4F; border-radius: 16px;"
        )

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._status_badge)
        layout.addStretch(1)

        self._api_ok = False
        self._socket_ok = False
        self._listening = False
        self._llm_source = None

    def _update_backend_status(self):
        ok = self._api_ok and self._socket_ok
        if not ok:
            self._status_badge.setText("● Offline")
            self._status_badge.setStyleSheet(
                "color: #ef4444; font-size: 13px; font-weight: 600; "
                "padding: 6px 12px; background: #2A1717; border: 1px solid #7F1D1D; border-radius: 16px;"
            )
            return

        if self._listening:
            self._status_badge.setText("● Listening")
            self._status_badge.setStyleSheet(
                "color: #ef4444; font-size: 13px; font-weight: 600; "
                "padding: 6px 12px; background: #2A1717; border: 1px solid #7F1D1D; border-radius: 16px;"
            )
        else:
            self._status_badge.setText("● Ready")
            self._status_badge.setStyleSheet(
                "color: #10b981; font-size: 13px; font-weight: 600; "
                "padding: 6px 12px; background: #172A22; border: 1px solid #1F6B4F; border-radius: 16px;"
            )

    def set_api_ok(self, ok: bool, status: str | None = None) -> None:
        self._api_ok = ok
        self._update_backend_status()

    def set_socket_connected(self, connected: bool) -> None:
        self._socket_ok = connected
        self._update_backend_status()

    def set_listening(self, listening: bool) -> None:
        self._listening = listening
        self._update_backend_status()

    def set_llm_source(self, source: str | None) -> None:
        self._llm_source = source

    def set_state(self, state: str) -> None:
        pass  # state is shown via orb and central layout now

    def set_confirmation_pending(self, pending: bool) -> None:
        pass  # shown via dialogs

