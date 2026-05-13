from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def apply_gaussian_blur_rgba(pixels: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return pixels
    img = Image.fromarray(np.clip(pixels * 255, 0, 255).astype('uint8'), mode='RGBA')
    out = img.filter(ImageFilter.GaussianBlur(radius=radius))
    return np.asarray(out, dtype=np.float32) / 255.0


def create_boundary_layer(composite: np.ndarray, width: int = 2, color=(1.0, 0.2, 0.2, 1.0)) -> np.ndarray:
    alpha = composite[..., 3]
    mask = (alpha > 0.02).astype(np.float32)
    dilated = mask.copy()
    for _ in range(max(width, 1)):
        padded = np.pad(dilated, 1)
        dilated = np.maximum.reduce([
            padded[1:-1,1:-1], padded[:-2,1:-1], padded[2:,1:-1], padded[1:-1,:-2], padded[1:-1,2:],
            padded[:-2,:-2], padded[:-2,2:], padded[2:,:-2], padded[2:,2:]
        ])
    edge = np.clip(dilated - mask, 0, 1)
    out = np.zeros_like(composite)
    out[..., 0] = color[0] * edge
    out[..., 1] = color[1] * edge
    out[..., 2] = color[2] * edge
    out[..., 3] = edge * color[3]
    return out


def create_text_layer(shape: tuple[int, int, int], text: str, font_path: str | None, size: int = 48) -> np.ndarray:
    h, w, _ = shape
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if font_path:
        try:
            font = ImageFont.truetype(font_path, size)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()
    draw.text((w // 8, h // 2), text or 'Text Layer', fill=(255,255,255,255), font=font)
    return np.asarray(img, dtype=np.float32) / 255.0


def apply_distortion_field(pixels: np.ndarray, center_x: float, center_y: float, dx: float, dy: float, strength: float) -> np.ndarray:
    h, w, _ = pixels.shape
    yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    dist = np.sqrt((xx-center_x)**2 + (yy-center_y)**2)
    drag_vec = np.array([dx, dy], dtype=np.float32)
    norm = np.linalg.norm(drag_vec) + 1e-6
    direction = drag_vec / norm
    to_px = np.stack([xx-center_x, yy-center_y], axis=-1)
    to_norm = to_px / (np.linalg.norm(to_px, axis=-1, keepdims=True) + 1e-6)
    directional_bias = np.maximum(np.sum(to_norm * direction, axis=-1), 0.2)
    weight = np.exp(-dist / max(strength, 1.0)) * directional_bias
    src_x = np.clip((xx - dx * weight).round().astype(int), 0, w-1)
    src_y = np.clip((yy - dy * weight).round().astype(int), 0, h-1)
    return pixels[src_y, src_x]
