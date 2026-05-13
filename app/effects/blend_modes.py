from __future__ import annotations

import numpy as np

EPS = 1e-6


def _clip(image: np.ndarray) -> np.ndarray:
    return np.clip(image, 0.0, 1.0)


def normal(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return blend


def darken(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return np.minimum(base, blend)


def lighten(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return np.maximum(base, blend)


def multiply(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return base * blend


def screen(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return 1.0 - ((1.0 - base) * (1.0 - blend))


def overlay(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return np.where(base < 0.5, 2.0 * base * blend, 1.0 - 2.0 * (1.0 - base) * (1.0 - blend))


def hard_light(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return overlay(blend, base)


def soft_light(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return np.where(
        blend < 0.5,
        2 * base * blend + (base * base) * (1 - 2 * blend),
        2 * base * (1 - blend) + np.sqrt(np.maximum(base, 0)) * (2 * blend - 1),
    )


def color_dodge(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return np.minimum(base / np.maximum(1.0 - blend, EPS), 1.0)


def color_burn(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return 1.0 - np.minimum((1.0 - base) / np.maximum(blend, EPS), 1.0)


def linear_dodge(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return base + blend


def linear_burn(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return base + blend - 1.0


def difference(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return np.abs(base - blend)


def exclusion(base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return base + blend - 2 * base * blend


BLEND_REGISTRY = {
    "normal": normal,
    "darken": darken,
    "lighten": lighten,
    "multiply": multiply,
    "screen": screen,
    "overlay": overlay,
    "hard_light": hard_light,
    "soft_light": soft_light,
    "color_dodge": color_dodge,
    "color_burn": color_burn,
    "linear_dodge": linear_dodge,
    "linear_burn": linear_burn,
    "difference": difference,
    "exclusion": exclusion,
}


def blend_mode_names() -> list[str]:
    return sorted(BLEND_REGISTRY.keys())


def apply_blend_mode(mode: str, base: np.ndarray, blend: np.ndarray) -> np.ndarray:
    fn = BLEND_REGISTRY.get(mode, normal)
    return _clip(fn(base, blend))
