from __future__ import annotations

import math

from PySide6 import QtCore, QtGui, QtWidgets


class OrbVisualizer(QtWidgets.QWidget):
    """Simple animated orb placeholder (V2 identity)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 180)
        self.setMaximumWidth(260)

        self._state = "IDLE"
        self._t = 0.0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60fps

    def set_state(self, state: str) -> None:
        self._state = state or "IDLE"
        self.update()

    def _tick(self):
        self._t += 0.016
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(12, 12, -12, -12)
        center = rect.center()
        radius = min(rect.width(), rect.height()) * 0.32

        speed = {
            "IDLE": 1.0,
            "LISTENING": 2.2,
            "THINKING": 2.6,
            "EXECUTING": 3.2,
            "RESPONDING": 2.0,
            "WAITING_CONFIRMATION": 1.6,
            "ERROR": 4.0,
        }.get(self._state, 1.0)

        breathe = 1.0 + 0.06 * math.sin(self._t * speed)
        r = radius * breathe

        # Base gradient (kept neutral; QSS/theme can override later).
        grad = QtGui.QRadialGradient(center, r * 1.6)
        grad.setColorAt(0.0, QtGui.QColor(180, 220, 255, 220))
        grad.setColorAt(0.55, QtGui.QColor(70, 140, 220, 140))
        grad.setColorAt(1.0, QtGui.QColor(20, 35, 55, 10))

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QBrush(grad))
        painter.drawEllipse(center, r, r)

        # State label
        painter.setPen(QtGui.QColor(200, 200, 200))
        painter.setFont(QtGui.QFont("Segoe UI", 9))
        painter.drawText(self.rect(), QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignBottom, self._state)
