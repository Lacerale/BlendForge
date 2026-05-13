from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class WarpPoint:
    x: float
    y: float
    original_x: float
    original_y: float
    locked: bool = False
    influence_weight: float = 1.0


class DistortionMesh:
    def __init__(self, width: int, height: int, rows: int = 6, cols: int = 6) -> None:
        self.width = width
        self.height = height
        self.rows = rows
        self.cols = cols
        self.points: list[WarpPoint] = []
        for r in range(rows):
            for c in range(cols):
                x = c * (width - 1) / (cols - 1)
                y = r * (height - 1) / (rows - 1)
                self.points.append(WarpPoint(x=x, y=y, original_x=x, original_y=y))

    def index(self, row: int, col: int) -> int:
        return row * self.cols + col

    def nearest_point(self, x: float, y: float, radius: float = 16.0) -> int | None:
        dmin = radius
        imin = None
        for i, p in enumerate(self.points):
            d = ((p.x - x) ** 2 + (p.y - y) ** 2) ** 0.5
            if d < dmin:
                dmin = d
                imin = i
        return imin

    def drag_point(self, idx: int, dx: float, dy: float, softness: float = 40.0, elasticity: float = 0.9) -> None:
        anchor = self.points[idx]
        if anchor.locked:
            return
        drag = np.array([dx, dy], dtype=np.float32)
        norm = np.linalg.norm(drag) + 1e-6
        drag_dir = drag / norm
        for p in self.points:
            vec = np.array([p.x - anchor.x, p.y - anchor.y], dtype=np.float32)
            dist = np.linalg.norm(vec)
            vdir = vec / (dist + 1e-6)
            directional = max(float(np.dot(vdir, drag_dir)), 0.2)
            anchor_resist = np.clip((p.original_y / max(self.height, 1)) ** 1.2, 0.05, 1.0)
            w = np.exp(-dist / max(softness, 1.0)) * directional * elasticity * anchor_resist
            if p is anchor:
                w = 1.0
            if not p.locked:
                p.x += dx * w
                p.y += dy * w

    def uv_maps(self) -> tuple[np.ndarray, np.ndarray]:
        # dense displacement field from inverse-distance interpolation over mesh nodes
        yy, xx = np.meshgrid(np.arange(self.height), np.arange(self.width), indexing='ij')
        src_x = xx.astype(np.float32)
        src_y = yy.astype(np.float32)
        accum_w = np.zeros((self.height, self.width), dtype=np.float32)
        delta_x = np.zeros((self.height, self.width), dtype=np.float32)
        delta_y = np.zeros((self.height, self.width), dtype=np.float32)
        for p in self.points:
            dx = p.x - p.original_x
            dy = p.y - p.original_y
            d2 = (xx - p.original_x) ** 2 + (yy - p.original_y) ** 2 + 1.0
            w = 1.0 / d2
            accum_w += w
            delta_x += w * dx
            delta_y += w * dy
        delta_x /= accum_w
        delta_y /= accum_w
        src_x = np.clip(src_x - delta_x, 0, self.width - 1)
        src_y = np.clip(src_y - delta_y, 0, self.height - 1)
        return src_x, src_y


def warp_image_with_mesh(pixels: np.ndarray, mesh: DistortionMesh) -> np.ndarray:
    src_x, src_y = mesh.uv_maps()
    x0 = np.floor(src_x).astype(int)
    y0 = np.floor(src_y).astype(int)
    return pixels[y0, x0]
