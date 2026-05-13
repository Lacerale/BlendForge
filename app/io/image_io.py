from __future__ import annotations

from pathlib import Path
import numpy as np
from PIL import Image


SUPPORTED_EXPORT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff"}


def load_image(path: str) -> np.ndarray:
    image = Image.open(path).convert("RGBA")
    arr = np.asarray(image, dtype=np.float32) / 255.0
    return np.ascontiguousarray(arr)


def save_image(path: str, pixels: np.ndarray) -> None:
    ext = Path(path).suffix.lower()
    if ext not in SUPPORTED_EXPORT_EXTENSIONS:
        raise ValueError(f"Unsupported export extension: {ext}")
    clipped = np.clip(pixels * 255.0, 0, 255).astype("uint8")
    mode = "RGBA"
    if ext in {".jpg", ".jpeg"}:
        mode = "RGB"
        clipped = clipped[..., :3]
    Image.fromarray(clipped, mode=mode).save(path)
