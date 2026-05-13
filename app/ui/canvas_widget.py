from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QImage, QPainter, QPen, QColor, QPolygonF
from PySide6.QtWidgets import QWidget

from app.selections.magic_wand import magic_wand_mask
from app.selections.selection_model import SelectionState
from app.tools.distortion_tool import DistortionMesh


class CanvasWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._image: QImage | None = None
        self._pixels: np.ndarray | None = None
        self._img_shape: tuple[int, int] | None = None
        self.distortion_mode = False
        self.mesh: DistortionMesh | None = None
        self.selected_point: int | None = None
        self.on_mesh_changed = None

        self.selection = SelectionState()

    def set_selection_mode(self, mode: str) -> None:
        self.selection.mode = mode
        self.selection.points.clear()
        self.update()

    def set_pixels(self, pixels: np.ndarray | None) -> None:
        self._pixels = pixels
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

    def _map_to_image(self, x: float, y: float) -> tuple[float, float] | None:
        if not self._image:
            return None
        iw, ih = self._image.width(), self._image.height()
        sx = iw / max(self.width(), 1)
        sy = ih / max(self.height(), 1)
        return x * sx, y * sy

    def mousePressEvent(self, event) -> None:  # noqa: N802
        mapped = self._map_to_image(event.position().x(), event.position().y())
        if mapped is None:
            return

        if self.selection.mode == "wand" and self._pixels is not None:
            self.selection.mask = magic_wand_mask(self._pixels, int(mapped[0]), int(mapped[1]))
            self.update()
            return

        if self.selection.mode in {"lasso", "polyline"}:
            self.selection.points.append(mapped)
            self.update()

        if self.distortion_mode and self.mesh:
            self.selected_point = self.mesh.nearest_point(mapped[0], mapped[1])

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        mapped = self._map_to_image(event.position().x(), event.position().y())
        if mapped is None:
            return

        if self.selection.mode == "lasso" and (event.buttons() & Qt.MouseButton.LeftButton):
            self.selection.points.append(mapped)
            self.update()

        if self.distortion_mode and self.mesh and self.selected_point is not None:
            px = self.mesh.points[self.selected_point]
            dx = mapped[0] - px.x
            dy = mapped[1] - px.y
            self.mesh.drag_point(self.selected_point, dx, dy)
            if self.on_mesh_changed:
                self.on_mesh_changed(self.mesh)
            self.update()

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if self.selection.mode == "polyline":
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self.selected_point = None

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().window())
        if self._image:
            painter.drawImage(self.rect(), self._image)

        if self._image and self.selection.points:
            sx = self.width() / max(self._image.width(), 1)
            sy = self.height() / max(self._image.height(), 1)
            painter.setPen(QPen(QColor('#ffffff'), 1, Qt.PenStyle.DashLine))
            poly = QPolygonF([QPointF(x * sx, y * sy) for x, y in self.selection.points])
            painter.drawPolyline(poly)

        if self._image and self.selection.mask is not None:
            sx = self.width() / max(self._image.width(), 1)
            sy = self.height() / max(self._image.height(), 1)
            ys, xs = np.where(self.selection.mask > 0.5)
            painter.setPen(QPen(QColor('#88c0ff'), 1))
            for y, x in zip(ys[::20], xs[::20]):
                painter.drawPoint(int(x * sx), int(y * sy))

        if self.distortion_mode and self.mesh and self._image:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor('#67a9ff'), 1))
            sx = self.width() / max(self._image.width(), 1)
            sy = self.height() / max(self._image.height(), 1)
            for r in range(self.mesh.rows):
                for c in range(self.mesh.cols - 1):
                    p1 = self.mesh.points[self.mesh.index(r, c)]
                    p2 = self.mesh.points[self.mesh.index(r, c + 1)]
                    painter.drawLine(p1.x * sx, p1.y * sy, p2.x * sx, p2.y * sy)
            for c in range(self.mesh.cols):
                for r in range(self.mesh.rows - 1):
                    p1 = self.mesh.points[self.mesh.index(r, c)]
                    p2 = self.mesh.points[self.mesh.index(r + 1, c)]
                    painter.drawLine(p1.x * sx, p1.y * sy, p2.x * sx, p2.y * sy)
            painter.setBrush(QColor('#8bd3ff'))
            for p in self.mesh.points:
                painter.drawEllipse(int(p.x * sx) - 3, int(p.y * sy) - 3, 6, 6)
