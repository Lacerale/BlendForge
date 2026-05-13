from __future__ import annotations

import numpy as np

from app.effects.blend_modes import apply_blend_mode
from app.effects.layer_effects import apply_gaussian_blur_rgba, apply_distortion_field
from app.layers.base_layer import Layer


class Compositor:
    def composite(self, layers: list[Layer]) -> np.ndarray | None:
        visible = [layer for layer in layers if layer.visible]
        if not visible:
            return None

        canvas = np.zeros_like(visible[0].pixels, dtype=np.float32)
        for layer in visible:
            layer_pixels = layer.pixels.astype(np.float32)

            if layer.distortion_strength > 0:
                layer_pixels = apply_distortion_field(layer_pixels, layer_pixels.shape[1] * 0.5, layer_pixels.shape[0] * 0.5, 18, 10, layer.distortion_strength)

            if layer.blur_radius > 0:
                layer_pixels = apply_gaussian_blur_rgba(layer_pixels, layer.blur_radius)

            if layer.mask is not None:
                mask = np.expand_dims(layer.mask, axis=-1)
                layer_pixels = layer_pixels * mask

            blended = apply_blend_mode(layer.blend_mode, canvas, layer_pixels)
            canvas = ((1.0 - layer.opacity) * canvas) + (layer.opacity * blended)
        return np.clip(canvas, 0.0, 1.0)
