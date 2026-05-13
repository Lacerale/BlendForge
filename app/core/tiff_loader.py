from __future__ import annotations

import numpy as np

from app.io.import_layers import _import_tiff_layers
from app.layers.base_layer import Layer


class TIFFLoader:
    @staticmethod
    def load_tiff(path: str) -> list[Layer]:
        layers = []
        for name, pixels, visible in _import_tiff_layers(path):
            layers.append(Layer(id=f"tiff-{len(layers)}", name=name, pixels=np.asarray(pixels, dtype=np.float32), visible=visible))
        return layers
