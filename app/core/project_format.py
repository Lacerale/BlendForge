from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from app.layers.base_layer import Layer


class ProjectFormat:
    @staticmethod
    def save(path: str, layers: list[Layer]) -> None:
        root = Path(path)
        root.mkdir(parents=True, exist_ok=True)
        layers_dir = root / 'layers'
        layers_dir.mkdir(exist_ok=True)

        metadata = {"layers": []}
        for idx, layer in enumerate(layers):
            file_name = f"{idx}.npy"
            np.save(layers_dir / file_name, layer.pixels)
            metadata["layers"].append({
                "name": layer.name,
                "visible": layer.visible,
                "opacity": layer.opacity,
                "blend_mode": layer.blend_mode,
                "file": file_name,
            })

        (root / 'metadata.json').write_text(json.dumps(metadata, indent=2))

    @staticmethod
    def load(path: str) -> list[Layer]:
        root = Path(path)
        metadata = json.loads((root / 'metadata.json').read_text())
        layers = []
        for idx, entry in enumerate(metadata.get('layers', [])):
            pixels = np.load(root / 'layers' / entry['file'])
            layers.append(Layer(
                id=f"proj-{idx}",
                name=entry.get('name', f'Layer {idx+1}'),
                pixels=pixels.astype(np.float32),
                visible=bool(entry.get('visible', True)),
                opacity=float(entry.get('opacity', 1.0)),
                blend_mode=str(entry.get('blend_mode', 'normal')),
            ))
        return layers
