from __future__ import annotations

import enum


class AssistantState(str, enum.Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    EXECUTING = "EXECUTING"
    RESPONDING = "RESPONDING"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    ERROR = "ERROR"
