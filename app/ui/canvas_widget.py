from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPen, QColor
from PySide6.QtWidgets import QWidget

from app.tools.distortion_tool import DistortionMesh


class CanvasWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._image: QImage | None = None
        self._img_shape: tuple[int,int] | None = None
        self.distortion_mode = False
        self.mesh: DistortionMesh | None = None
        self.selected_point: int | None = None
        self.on_mesh_changed = None

    def set_pixels(self, pixels: np.ndarray | None) -> None:
        if pixels is None:
            self._image = None
            self._img_shape = None
            self.update(); return
        h, w, _ = pixels.shape
        self._img_shape = (h, w)
        data = np.clip(pixels * 255.0, 0, 255).astype("uint8")
        self._image = QImage(data.data, w, h, 4 * w, QImage.Format_RGBA8888).copy()
        if self.distortion_mode and self.mesh is None:
            self.mesh = DistortionMesh(w, h, 6, 6)
        self.update()

    def set_distortion_mode(self, enabled: bool) -> None:
        self.distortion_mode = enabled
        if not enabled:
            self.mesh = None
        elif self._img_shape and self.mesh is None:
            h, w = self._img_shape
            self.mesh = DistortionMesh(w, h, 6, 6)
        self.update()

    def _map_to_image(self, x: float, y: float) -> tuple[float,float] | None:
        if not self._image:
            return None
        iw, ih = self._image.width(), self._image.height()
        sx = iw / max(self.width(), 1)
        sy = ih / max(self.height(), 1)
        return x * sx, y * sy

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if not self.distortion_mode or not self.mesh:
            return
        mapped = self._map_to_image(event.position().x(), event.position().y())
        if not mapped:
            return
        self.selected_point = self.mesh.nearest_point(mapped[0], mapped[1])

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if not self.distortion_mode or not self.mesh or self.selected_point is None:
            return
        mapped = self._map_to_image(event.position().x(), event.position().y())
        if not mapped:
            return
        px = self.mesh.points[self.selected_point]
        dx = mapped[0] - px.x
        dy = mapped[1] - px.y
        self.mesh.drag_point(self.selected_point, dx, dy)
        if self.on_mesh_changed:
            self.on_mesh_changed(self.mesh)
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self.selected_point = None

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().window())
        if self._image:
            painter.drawImage(self.rect(), self._image)

        if self.distortion_mode and self.mesh and self._image:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(QColor('#67a9ff'), 1)
            painter.setPen(pen)
            sx = self.width() / max(self._image.width(), 1)
            sy = self.height() / max(self._image.height(), 1)
            # grid lines
            for r in range(self.mesh.rows):
                for c in range(self.mesh.cols-1):
                    p1 = self.mesh.points[self.mesh.index(r,c)]
                    p2 = self.mesh.points[self.mesh.index(r,c+1)]
                    painter.drawLine(p1.x*sx, p1.y*sy, p2.x*sx, p2.y*sy)
            for c in range(self.mesh.cols):
                for r in range(self.mesh.rows-1):
                    p1 = self.mesh.points[self.mesh.index(r,c)]
                    p2 = self.mesh.points[self.mesh.index(r+1,c)]
                    painter.drawLine(p1.x*sx, p1.y*sy, p2.x*sx, p2.y*sy)
            painter.setBrush(QColor('#8bd3ff'))
            for p in self.mesh.points:
                painter.drawEllipse(int(p.x*sx)-3, int(p.y*sy)-3, 6, 6)
