from __future__ import annotations

from pathlib import Path
import numpy as np

from app.io.image_io import load_image


def _import_psd_layers(path: str) -> list[tuple[str, np.ndarray]]:
    try:
        from psd_tools import PSDImage
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError('PSD import requires psd-tools. Install with: pip install psd-tools') from exc

    psd = PSDImage.open(path)
    layers: list[tuple[str, np.ndarray]] = []
    for layer in psd:
        if not layer.is_visible():
            continue
        pil = layer.composite()
        if pil is None:
            continue
        arr = np.asarray(pil.convert('RGBA'), dtype=np.float32) / 255.0
        layers.append((layer.name or 'Layer', arr))
    return layers


def _import_tiff_layers(path: str) -> list[tuple[str, np.ndarray]]:
    # Prefer true multi-page TIFF import via tifffile.
    try:
        import tifffile  # type: ignore

        with tifffile.TiffFile(path) as tif:
            layers: list[tuple[str, np.ndarray]] = []
            for i, page in enumerate(tif.pages):
                arr = page.asarray()
                if arr.ndim == 2:
                    arr = np.stack([arr, arr, arr, np.full_like(arr, 255)], axis=-1)
                elif arr.ndim == 3 and arr.shape[-1] == 3:
                    alpha = np.full(arr.shape[:2] + (1,), 255, dtype=arr.dtype)
                    arr = np.concatenate([arr, alpha], axis=-1)
                elif arr.ndim == 3 and arr.shape[-1] == 4:
                    pass
                else:
                    continue
                arrf = np.asarray(arr, dtype=np.float32) / 255.0
                layers.append((f"TIFF Page {i+1}", arrf))
            if layers:
                return layers
    except Exception:
        pass

    # Fallback: PIL sequence frames
    from PIL import Image, ImageSequence

    image = Image.open(path)
    layers = []
    for i, frame in enumerate(ImageSequence.Iterator(image)):
        arr = np.asarray(frame.convert('RGBA'), dtype=np.float32) / 255.0
        layers.append((f"TIFF Frame {i+1}", arr))
    return layers


def import_layers_from_file(path: str) -> list[tuple[str, np.ndarray]]:
    ext = Path(path).suffix.lower()
    if ext == '.psd':
        layers = _import_psd_layers(path)
        if layers:
            return layers
    if ext in {'.tif', '.tiff'}:
        layers = _import_tiff_layers(path)
        if layers:
            return layers
    return [(Path(path).name, load_image(path))]
