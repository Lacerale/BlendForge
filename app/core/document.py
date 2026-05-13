from __future__ import annotations

import uuid
import numpy as np

from app.core.history import HistoryState
from app.effects.layer_effects import create_boundary_layer, create_text_layer
from app.layers.base_layer import Layer
from app.layers.layer_manager import LayerManager
from app.renderer.compositor import Compositor


class Document:
    def __init__(self) -> None:
        self.layer_manager = LayerManager()
        self.compositor = Compositor()
        self.history = HistoryState()

    def add_image_layer(self, pixels: np.ndarray, name: str = "Layer") -> Layer:
        if pixels.dtype != np.float32:
            pixels = pixels.astype(np.float32)
        layer = Layer(id=str(uuid.uuid4()), name=name, pixels=pixels)
        self.layer_manager.add_layer(layer)
        self.history.push(f"Added layer {name}")
        return layer

    def add_text_layer(self, shape: tuple[int, int, int], text: str, font_path: str | None) -> Layer:
        pixels = create_text_layer(shape, text, font_path)
        layer = Layer(id=str(uuid.uuid4()), name="Text", pixels=pixels, is_text_layer=True, text_content=text, font_path=font_path)
        self.layer_manager.add_layer(layer)
        self.history.push("Added text layer")
        return layer

    def add_boundary_layer(self, width: int = 2) -> Layer | None:
        composite = self.render()
        if composite is None:
            return None
        boundary = create_boundary_layer(composite, width)
        layer = Layer(id=str(uuid.uuid4()), name="Boundary", pixels=boundary, boundary_width=width)
        self.layer_manager.add_layer(layer)
        self.history.push("Added boundary layer")
        return layer

    def toggle_visibility(self, layer_id: str) -> None:
        layer = self.layer_manager.get_layer(layer_id)
        if not layer:
            raise ValueError(f"Layer not found: {layer_id}")
        layer.visible = not layer.visible
        layer.dirty = True
        self.history.push(f"Toggled visibility for {layer.name}")

    def render(self) -> np.ndarray | None:
        return self.compositor.composite(self.layer_manager.layers)
