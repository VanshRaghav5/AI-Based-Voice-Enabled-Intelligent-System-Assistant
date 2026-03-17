from __future__ import annotations

from typing import Any, Callable, Dict, Optional


_emitter: Optional[Callable[[str, Dict[str, Any]], None]] = None


def set_emitter(emitter: Optional[Callable[[str, Dict[str, Any]], None]]) -> None:
    """Set a process-wide event emitter for runtime UI events.

    The emitter should be safe to call from background threads.

    Example emitter for Flask-SocketIO:
        lambda event, payload: socketio.emit(event, payload)
    """

    global _emitter
    _emitter = emitter


def emit(event: str, payload: Dict[str, Any]) -> None:
    """Emit an event if an emitter is configured."""

    if not _emitter:
        return

    try:
        _emitter(event, payload)
    except Exception:
        # Runtime UI telemetry must never break tool execution.
        return
