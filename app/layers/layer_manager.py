from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from app.layers.base_layer import Layer


@dataclass
class LayerManager:
    layers: list[Layer] = field(default_factory=list)

    def add_layer(self, layer: Layer) -> None:
        self.layers.append(layer)

    def remove_layer(self, layer_id: str) -> None:
        self.layers = [layer for layer in self.layers if layer.id != layer_id]

    def move_layer(self, from_index: int, to_index: int) -> None:
        if from_index < 0 or from_index >= len(self.layers):
            raise IndexError("from_index out of bounds")
        if to_index < 0 or to_index >= len(self.layers):
            raise IndexError("to_index out of bounds")
        layer = self.layers.pop(from_index)
        self.layers.insert(to_index, layer)

    def get_layer(self, layer_id: str) -> Layer | None:
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        return None

    def visible_layers(self) -> Iterable[Layer]:
        return (layer for layer in self.layers if layer.visible)
