from __future__ import annotations

import math
import time

from PySide6 import QtCore, QtGui, QtWidgets


class WaveformWidget(QtWidgets.QWidget):
    """Smooth overlapping sine wave animation representing listening state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 30)
        
        self._phase = 0.0
        self._amplitude = 1.0
        
        # Timer for smooth animation ~60fps
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.setInterval(16)

    def start(self):
        self._phase = 0.0
        self.timer.start()
        self.show()

    def stop(self):
        self.timer.stop()
        self.hide()

    def _animate(self):
        self._phase += 0.15
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)

        rect = self.rect()
        width = rect.width()
        height = rect.height()
        mid_y = height / 2.0

        painter.setPen(QtCore.Qt.PenStyle.NoPen)

        # Draw a few overlapping sine waves
        waves = [
            {"color": QtGui.QColor(59, 130, 246, 100), "freq": 1.0, "speed": 1.0, "amp": 0.5},
            {"color": QtGui.QColor(16, 185, 129, 100), "freq": 1.5, "speed": 1.3, "amp": 0.8},
            {"color": QtGui.QColor(139, 92, 246, 100), "freq": 2.0, "speed": 0.8, "amp": 0.6},
        ]

        for wave in waves:
            path = QtGui.QPainterPath()
            path.moveTo(0, mid_y)
            
            for x in range(0, width + 5, 5):
                # Normalize x to 0..1
                nx = x / width
                
                # Attenuate the edges so the wave starts and ends at mid_y smoothly
                attenuation = math.sin(nx * math.pi)
                
                y_offset = math.sin((nx * math.pi * 2 * wave["freq"]) + (self._phase * wave["speed"]))
                y = mid_y + (y_offset * (height / 2.0) * wave["amp"] * attenuation * self._amplitude)
                
                path.lineTo(x, y)
                
            path.lineTo(width, height)
            path.lineTo(0, height)
            path.closeSubpath()
            
            painter.setBrush(QtGui.QBrush(wave["color"]))
            painter.drawPath(path)
