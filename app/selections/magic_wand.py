from __future__ import annotations

from collections import deque
import numpy as np


def magic_wand_mask(image: np.ndarray, sx: int, sy: int, tolerance: float = 0.12) -> np.ndarray:
    h, w, _ = image.shape
    sx = max(0, min(w - 1, sx))
    sy = max(0, min(h - 1, sy))
    target = image[sy, sx, :3]
    mask = np.zeros((h, w), dtype=np.uint8)
    q: deque[tuple[int, int]] = deque([(sx, sy)])
    mask[sy, sx] = 1
    while q:
        x, y = q.popleft()
        for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if nx < 0 or ny < 0 or nx >= w or ny >= h or mask[ny, nx]:
                continue
            d = np.linalg.norm(image[ny, nx, :3] - target)
            if d <= tolerance:
                mask[ny, nx] = 1
                q.append((nx, ny))
    return mask.astype(np.float32)
