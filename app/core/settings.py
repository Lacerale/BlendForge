from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppSettings:
    default_blend_mode: str = "normal"
    default_opacity: float = 1.0
