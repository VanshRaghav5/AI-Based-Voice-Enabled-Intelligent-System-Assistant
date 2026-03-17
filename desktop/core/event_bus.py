from __future__ import annotations

from PySide6 import QtCore


class EventBus(QtCore.QObject):
    """Thread-safe signal hub for background services → UI."""

    state_changed = QtCore.Signal(str)

    connection_status = QtCore.Signal(dict)  # {status, listening, pending_confirmation, wake_word_active}
    status_changed = QtCore.Signal(dict)  # generic status dict updates

    message = QtCore.Signal(dict)  # {role, text, meta?}

    execution_step = QtCore.Signal(dict)  # {step, description, status}
    command_result = QtCore.Signal(dict)  # backend result
    error = QtCore.Signal(dict)  # {message, ...}

    confirmation_required = QtCore.Signal(dict)
    confirmation_result = QtCore.Signal(dict)

    voice_input = QtCore.Signal(dict)  # {text, final}
    listening_status = QtCore.Signal(dict)  # {listening, triggered_by_wake_word?}
    wake_word_status = QtCore.Signal(dict)  # {active}
    wake_word_detected = QtCore.Signal(dict)  # {word}

    speech_complete = QtCore.Signal(dict)  # {text}
    assistant_shutdown = QtCore.Signal(dict)  # {message}
