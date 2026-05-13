from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class Layer:
    id: str
    name: str
    pixels: np.ndarray
    visible: bool = True
    locked: bool = False
    opacity: float = 1.0
    blend_mode: str = "normal"
    mask: np.ndarray | None = None

    blur_radius: int = 0
    directional_blur_angle: float = 0.0
    distortion_strength: float = 0.0

    is_text_layer: bool = False
    text_content: str = ""
    font_path: str | None = None
    boundary_width: int = 0

    dirty: bool = True
    cached_result: np.ndarray | None = field(default=None, repr=False)
