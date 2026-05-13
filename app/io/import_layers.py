from __future__ import annotations

from pathlib import Path
import numpy as np

from app.io.image_io import load_image

ImportedLayer = tuple[str, np.ndarray, bool]


def _as_rgba(arr: np.ndarray) -> np.ndarray | None:
    if arr.ndim == 2:
        return np.stack([arr, arr, arr, np.full_like(arr, 255)], axis=-1)
    if arr.ndim == 3 and arr.shape[-1] == 3:
        alpha = np.full(arr.shape[:2] + (1,), 255, dtype=arr.dtype)
        return np.concatenate([arr, alpha], axis=-1)
    if arr.ndim == 3 and arr.shape[-1] == 4:
        return arr
    return None


def _flatten_psd_layers(psd_layer, out: list[ImportedLayer], prefix: str = "") -> None:
    name = f"{prefix}{psd_layer.name or 'Layer'}"
    if psd_layer.is_group():
        for child in psd_layer:
            _flatten_psd_layers(child, out, prefix=f"{name}/")
        return
    pil = psd_layer.composite()
    if pil is None:
        return
    arr = np.asarray(pil.convert('RGBA'), dtype=np.float32) / 255.0
    out.append((name, arr, bool(psd_layer.is_visible())))


def _import_psd_layers(path: str) -> list[ImportedLayer]:
    from psd_tools import PSDImage
    psd = PSDImage.open(path)
    layers: list[ImportedLayer] = []
    for layer in psd:
        _flatten_psd_layers(layer, layers)
    return layers


def _import_tiff_layers(path: str) -> list[ImportedLayer]:
    import tifffile  # type: ignore

    layers: list[ImportedLayer] = []
    with tifffile.TiffFile(path) as tif:
        # 1) direct pages + subifds (common layered/stack tiffs)
        for i, page in enumerate(tif.pages):
            try:
                arr = page.asarray()
                rgba = _as_rgba(arr)
                if rgba is not None:
                    n = page.tags.get('PageName').value if page.tags.get('PageName') else f"TIFF Page {i+1}"
                    layers.append((str(n), rgba.astype(np.float32) / 255.0, True))
            except Exception:
                pass

            subifds = getattr(page, 'pages', None)
            if subifds:
                for j, sp in enumerate(subifds):
                    try:
                        arr = sp.asarray()
                        rgba = _as_rgba(arr)
                        if rgba is not None:
                            layers.append((f"TIFF SubIFD {i+1}.{j+1}", rgba.astype(np.float32) / 255.0, True))
                    except Exception:
                        continue

        if layers:
            return layers

        # 2) series/axes fallback (OME, ImageJ, hyperstacks)
        for si, series in enumerate(tif.series):
            try:
                arr = series.asarray()
            except Exception:
                continue
            # Try flattening first dimensions into layer planes.
            if arr.ndim >= 4:
                planes = arr.reshape((-1,) + arr.shape[-3:])
            elif arr.ndim == 3:
                planes = arr.reshape((-1,) + arr.shape[-2:] + (1,)) if arr.shape[-1] not in (3,4) else arr[np.newaxis, ...]
            else:
                planes = arr[np.newaxis, ...]

            for pi, plane in enumerate(planes):
                rgba = _as_rgba(plane)
                if rgba is None:
                    continue
                layers.append((f"TIFF Series {si+1} Plane {pi+1}", rgba.astype(np.float32) / 255.0, True))

    if layers:
        return layers

    # 3) Pillow fallback
    from PIL import Image, ImageSequence
    image = Image.open(path)
    for i, frame in enumerate(ImageSequence.Iterator(image)):
        arr = np.asarray(frame.convert('RGBA'), dtype=np.float32) / 255.0
        layers.append((f"TIFF Frame {i+1}", arr, True))
    return layers


def import_layers_from_file(path: str) -> list[ImportedLayer]:
    ext = Path(path).suffix.lower()
    if ext == '.psd':
        try:
            layers = _import_psd_layers(path)
            if layers:
                return layers
        except Exception:
            pass
    if ext in {'.tif', '.tiff'}:
        try:
            layers = _import_tiff_layers(path)
            if layers:
                return layers
        except Exception:
            pass
    return [(Path(path).name, load_image(path), True)]
