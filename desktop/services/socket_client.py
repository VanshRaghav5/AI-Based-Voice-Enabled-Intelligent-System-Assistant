from __future__ import annotations

from typing import Any, Callable, Dict, Optional

import socketio

from desktop.core.event_bus import EventBus
from desktop.services.session_store import SessionStore


class SocketClient:
    """Socket.IO client that forwards events onto a Qt EventBus."""

    def __init__(self, socket_url: str, session: SessionStore, bus: EventBus):
        self.socket_url = socket_url.rstrip("/")
        self.session = session
        self.bus = bus

        self.sio = socketio.Client(reconnection=True, reconnection_attempts=0, reconnection_delay=1)
        self._register_default_handlers()

    def _register(self, event: str, handler: Callable[..., Any]) -> None:
        self.sio.on(event, handler)

    def _register_default_handlers(self) -> None:
        @self.sio.event
        def connect():
            self.bus.status_changed.emit({"socket": "connected"})

        @self.sio.event
        def connect_error(data):
            message = str(data or "Socket authentication failed")
            lower = message.lower()
            if "token" in lower and ("expired" in lower or "invalid" in lower):
                self.session.clear()
                self.bus.error.emit({
                    "message": "Session expired. Please sign in again.",
                    "code": "unauthorized",
                })
                try:
                    self.sio.disconnect()
                except Exception:
                    pass
                return
            self.bus.error.emit({"message": f"Socket connect failed: {message}"})

        @self.sio.event
        def disconnect():
            self.bus.status_changed.emit({"socket": "disconnected"})

        @self.sio.on("connection_status")
        def on_connection_status(data):
            if isinstance(data, dict):
                self.bus.connection_status.emit(data)

        @self.sio.on("execution_step")
        def on_execution_step(data):
            if isinstance(data, dict):
                self.bus.execution_step.emit(data)

        @self.sio.on("command_result")
        def on_command_result(data):
            if isinstance(data, dict):
                self.bus.command_result.emit(data)

        @self.sio.on("error")
        def on_error(data):
            if isinstance(data, dict):
                self.bus.error.emit(data)
            else:
                self.bus.error.emit({"message": str(data)})

        @self.sio.on("confirmation_required")
        def on_confirmation_required(data):
            if isinstance(data, dict):
                self.bus.confirmation_required.emit(data)

        @self.sio.on("confirmation_result")
        def on_confirmation_result(data):
            if isinstance(data, dict):
                self.bus.confirmation_result.emit(data)

        @self.sio.on("voice_input")
        def on_voice_input(data):
            if isinstance(data, dict):
                self.bus.voice_input.emit(data)

        @self.sio.on("listening_status")
        def on_listening_status(data):
            if isinstance(data, dict):
                self.bus.listening_status.emit(data)

        @self.sio.on("wake_word_status")
        def on_wake_word_status(data):
            if isinstance(data, dict):
                self.bus.wake_word_status.emit(data)

        @self.sio.on("wake_word_detected")
        def on_wake_word_detected(data):
            if isinstance(data, dict):
                self.bus.wake_word_detected.emit(data)

        @self.sio.on("speech_complete")
        def on_speech_complete(data):
            if isinstance(data, dict):
                self.bus.speech_complete.emit(data)

        @self.sio.on("assistant_shutdown")
        def on_assistant_shutdown(data):
            if isinstance(data, dict):
                self.bus.assistant_shutdown.emit(data)

    def connect(self) -> bool:
        if self.sio.connected:
            return True

        token = self.session.token
        if not token:
            self.bus.error.emit({"message": "Missing auth token", "code": "unauthorized"})
            return False

        try:
            self.sio.connect(self.socket_url, auth={"token": token})
            return True
        except Exception as exc:
            self.bus.error.emit({"message": f"Socket connect failed: {exc}"})
            return False

    def disconnect(self) -> None:
        try:
            if self.sio.connected:
                self.sio.disconnect()
        except Exception:
            pass

    @property
    def connected(self) -> bool:
        return self.sio.connected
