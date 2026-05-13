from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class SelectionState:
    mode: str = "none"  # none|lasso|polyline|wand
    points: list[tuple[float, float]] = field(default_factory=list)
    mask: np.ndarray | None = None

    def clear(self) -> None:
        self.points.clear()
        self.mask = None
