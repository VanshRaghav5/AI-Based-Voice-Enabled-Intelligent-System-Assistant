from __future__ import annotations

import math
from PySide6 import QtCore, QtGui, QtWidgets

class OrbVisualizer(QtWidgets.QWidget):
    """Animated orb placeholder using QPropertyAnimation and QTimer for dynamic states."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 180)
        self.setMaximumWidth(260)

        self._state = "IDLE"
        self._current_scale = 1.0
        self._rotation_angle = 0.0
        self._wave_phase = 0.0
        self._idle_breath_phase = 0.0
        self._listen_ring_offset = 0.0
        self._opacity_value = 1.0

        self._opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self.animation = QtCore.QPropertyAnimation(self, b"scale")
        self.opacity_animation = QtCore.QPropertyAnimation(self, b"orbOpacity")
        self._apply_animation()
        
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.timeout.connect(self._on_timer_tick)
        self.update_timer.start(16)

    @QtCore.Property(float)
    def scale(self):
        return self._current_scale

    @scale.setter
    def scale(self, value: float):
        try:
            self._current_scale = value
            self.update()
        except RuntimeError:
            # C++ object has been deleted
            pass

    @QtCore.Property(float)
    def orbOpacity(self):
        return self._opacity_value

    @orbOpacity.setter
    def orbOpacity(self, value: float):
        self._opacity_value = max(0.35, min(1.0, value))
        try:
            self._opacity_effect.setOpacity(self._opacity_value)
            self.update()
        except RuntimeError:
            pass
            
    def _on_timer_tick(self):
        needs_update = False
        try:
            if self._state in ["THINKING", "EXECUTING"]:
                self._rotation_angle = (self._rotation_angle + 3.5) % 360
                needs_update = True
            elif self._state == "RESPONDING":
                self._wave_phase = (self._wave_phase + 0.16) % (math.pi * 2)
                needs_update = True
            elif self._state == "LISTENING":
                self._listen_ring_offset = (self._listen_ring_offset + 1.6) % 42
                needs_update = True
            else:
                self._idle_breath_phase = (self._idle_breath_phase + 0.04) % (math.pi * 2)
                needs_update = True
                
            if needs_update:
                self.update()
        except RuntimeError:
            pass

    def set_state(self, state: str) -> None:
        if self._state == state:
            return
        self._state = state or "IDLE"
        self._apply_animation()

    def _apply_animation(self):
        self.animation.stop()
        self.opacity_animation.stop()

        if self._state == "LISTENING":
            start_val, max_val, duration = 0.96, 1.2, 600
            op_start, op_peak, op_duration = 0.74, 1.0, 600
        elif self._state in ["THINKING", "EXECUTING"]:
            start_val, max_val, duration = 0.98, 1.12, 1100
            op_start, op_peak, op_duration = 0.82, 0.98, 1100
        elif self._state == "RESPONDING":
            start_val, max_val, duration = 1.0, 1.12, 820
            op_start, op_peak, op_duration = 0.86, 1.0, 820
        elif self._state == "ERROR":
            start_val, max_val, duration = 0.96, 1.2, 380
            op_start, op_peak, op_duration = 0.72, 1.0, 380
        else:
            # Idle: slow breathing glow.
            start_val, max_val, duration = 0.99, 1.06, 2800
            op_start, op_peak, op_duration = 0.9, 1.0, 2800

        self.animation.setDuration(duration)
        self.animation.setLoopCount(-1)
        self.animation.setKeyValueAt(0, start_val)
        self.animation.setKeyValueAt(0.5, max_val)
        self.animation.setKeyValueAt(1.0, start_val)

        self.opacity_animation.setDuration(op_duration)
        self.opacity_animation.setLoopCount(-1)
        self.opacity_animation.setKeyValueAt(0.0, op_start)
        self.opacity_animation.setKeyValueAt(0.5, op_peak)
        self.opacity_animation.setKeyValueAt(1.0, op_start)
        
        self.animation.start()
        self.opacity_animation.start()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(12, 12, -12, -12)
        center = rect.center()
        base_radius = min(rect.width(), rect.height()) * 0.32

        r = base_radius * self._current_scale

        if self._state == "RESPONDING":
            # Speaking: wave ripple animation.
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            for i in range(4):
                ripple_r = r + (i * 16) + (math.sin(self._wave_phase + (i * 0.7)) * 10)
                alpha = max(0, 170 - int(abs(ripple_r - base_radius) * 1.45))
                
                grad = QtGui.QRadialGradient(center, ripple_r)
                grad.setColorAt(0.0, QtGui.QColor(120, 215, 255, alpha))
                grad.setColorAt(0.55, QtGui.QColor(70, 170, 255, int(alpha / 1.45)))
                grad.setColorAt(1.0, QtGui.QColor(70, 160, 255, 0))
                
                painter.setBrush(QtGui.QBrush(grad))
                painter.drawEllipse(center, ripple_r, ripple_r)

        if self._state == "LISTENING":
            # Listening: concentric pulse rings.
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            for i in range(3):
                ring_r = r + (i * 14) + self._listen_ring_offset
                ring_alpha = max(0, 150 - int((ring_r - r) * 4.5))
                ring = QtGui.QRadialGradient(center, ring_r)
                ring.setColorAt(0.0, QtGui.QColor(90, 255, 190, int(ring_alpha * 0.18)))
                ring.setColorAt(0.78, QtGui.QColor(90, 255, 190, ring_alpha))
                ring.setColorAt(1.0, QtGui.QColor(90, 255, 190, 0))
                painter.setBrush(QtGui.QBrush(ring))
                painter.drawEllipse(center, ring_r, ring_r)

        grad = QtGui.QRadialGradient(center, r * 1.6)
        
        # Color changes based on state
        if self._state == "ERROR":
            c1, c2 = QtGui.QColor(255, 100, 100, 220), QtGui.QColor(220, 70, 70, 140)
        elif self._state == "LISTENING":
            c1, c2 = QtGui.QColor(100, 255, 180, 230), QtGui.QColor(70, 220, 140, 150)
        elif self._state in ["THINKING", "EXECUTING"]:
            c1, c2 = QtGui.QColor(220, 180, 255, 230), QtGui.QColor(180, 140, 220, 150)
        else:
            c1, c2 = QtGui.QColor(100, 200, 255, 220), QtGui.QColor(70, 140, 220, 140)

        if self._state in ["THINKING", "EXECUTING"]:
            # Rotate focal point for thinking glow effect
            rad = math.radians(self._rotation_angle)
            offset = base_radius * 0.4
            grad.setFocalPoint(center.x() + math.cos(rad) * offset, center.y() + math.sin(rad) * offset)
            r = r * 1.2 # Make it slightly larger to prevent clipping out of gradient
        elif self._state == "IDLE":
            # Idle breathing: gentle center drift to avoid static look.
            drift = math.sin(self._idle_breath_phase) * base_radius * 0.1
            grad.setFocalPoint(center.x() + drift, center.y() - drift * 0.45)

        grad.setColorAt(0.0, c1)
        grad.setColorAt(0.55, c2)
        grad.setColorAt(1.0, QtGui.QColor(20, 35, 55, 0))

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QBrush(grad))
        painter.drawEllipse(center, r, r)
