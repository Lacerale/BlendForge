from __future__ import annotations

import math
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QPolygonF
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QWidget


class DirectionalKnob(QWidget):
    angleChanged = Signal(float)

    def __init__(self) -> None:
        super().__init__()
        self._angle = 0.0
        self.setMinimumSize(92, 92)
        self.setMaximumSize(140, 140)

    @property
    def angle(self) -> float:
        return self._angle

    def set_angle(self, angle: float) -> None:
        self._angle = angle % 360.0
        self.angleChanged.emit(self._angle)
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._update_angle(event.position().x(), event.position().y())

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._update_angle(event.position().x(), event.position().y())

    def _update_angle(self, x: float, y: float) -> None:
        cx, cy = self.width() / 2, self.height() / 2
        radians = math.atan2(y - cy, x - cx)
        self.set_angle((math.degrees(radians) + 90.0) % 360.0)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = min(self.width(), self.height()) / 2 - 8
        center = QPointF(self.width() / 2, self.height() / 2)

        painter.setPen(QPen(QColor('#6a6f7b'), 2))
        painter.setBrush(QColor('#2a2d33'))
        painter.drawEllipse(center, r, r)

        theta = math.radians(self._angle - 90.0)
        tip = QPointF(center.x() + r * math.cos(theta), center.y() + r * math.sin(theta))
        left = QPointF(center.x() + (r - 12) * math.cos(theta + 0.35), center.y() + (r - 12) * math.sin(theta + 0.35))
        right = QPointF(center.x() + (r - 12) * math.cos(theta - 0.35), center.y() + (r - 12) * math.sin(theta - 0.35))

        painter.setPen(QPen(QColor('#8ab4ff'), 3))
        painter.drawLine(center, tip)
        painter.setBrush(QColor('#8ab4ff'))
        painter.drawPolygon(QPolygonF([tip, left, right]))
