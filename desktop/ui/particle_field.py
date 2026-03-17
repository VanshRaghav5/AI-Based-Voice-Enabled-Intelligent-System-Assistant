from __future__ import annotations

import math
import random
from dataclasses import dataclass

from PySide6 import QtCore, QtGui, QtWidgets


@dataclass
class _Particle:
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    alpha: int
    twinkle_phase: float
    twinkle_speed: float


class ParticleField(QtWidgets.QWidget):
    """Lightweight animated particle layer for subtle premium background depth."""

    def __init__(self, parent: QtWidgets.QWidget | None = None, particle_count: int = 40):
        super().__init__(parent)
        self._particle_count = max(12, min(96, particle_count))
        self._particles: list[_Particle] = []
        self._rng = random.Random()

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(33)  # ~30 FPS
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        self._spawn_particles()

    def _spawn_particles(self) -> None:
        w = max(1, self.width())
        h = max(1, self.height())
        self._particles = [self._new_particle(w, h) for _ in range(self._particle_count)]

    def _new_particle(self, w: int, h: int) -> _Particle:
        speed_x = self._rng.uniform(-0.20, 0.20)
        speed_y = self._rng.uniform(-0.16, 0.16)
        return _Particle(
            x=self._rng.uniform(0, w),
            y=self._rng.uniform(0, h),
            vx=speed_x,
            vy=speed_y,
            radius=self._rng.uniform(1.4, 3.2),
            alpha=self._rng.randint(46, 126),
            twinkle_phase=self._rng.uniform(0.0, math.tau),
            twinkle_speed=self._rng.uniform(0.045, 0.095),
        )

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        if not self._particles:
            self._spawn_particles()

    def _tick(self) -> None:
        w = max(1, self.width())
        h = max(1, self.height())
        if w <= 1 or h <= 1:
            return

        for p in self._particles:
            p.x += p.vx
            p.y += p.vy
            p.twinkle_phase += p.twinkle_speed
            if p.twinkle_phase > math.tau:
                p.twinkle_phase -= math.tau

            if p.x < -4:
                p.x = w + 2
            elif p.x > w + 4:
                p.x = -2

            if p.y < -4:
                p.y = h + 2
            elif p.y > h + 4:
                p.y = -2

        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)
        if not self._particles:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        # Soft mesh lines make movement noticeable without becoming noisy.
        max_dist = 140.0
        for i, p1 in enumerate(self._particles):
            for p2 in self._particles[i + 1:]:
                dx = p1.x - p2.x
                dy = p1.y - p2.y
                dist = math.hypot(dx, dy)
                if dist <= max_dist:
                    ratio = 1.0 - (dist / max_dist)
                    alpha = int(10 + (44 * ratio))
                    pen = QtGui.QPen(QtGui.QColor(84, 147, 255, alpha), 1.0)
                    painter.setPen(pen)
                    painter.drawLine(QtCore.QPointF(p1.x, p1.y), QtCore.QPointF(p2.x, p2.y))

        for p in self._particles:
            twinkle = 0.65 + (0.35 * ((math.sin(p.twinkle_phase) + 1.0) * 0.5))
            dynamic_alpha = min(180, max(38, int(p.alpha * twinkle)))

            glow_color = QtGui.QColor(84, 147, 255, int(dynamic_alpha * 0.35))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(glow_color)
            painter.drawEllipse(QtCore.QPointF(p.x, p.y), p.radius * 2.1, p.radius * 2.1)

            color = QtGui.QColor(124, 187, 255, dynamic_alpha)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QtCore.QPointF(p.x, p.y), p.radius, p.radius)
