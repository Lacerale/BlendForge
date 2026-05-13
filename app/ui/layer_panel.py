from __future__ import annotations

from PySide6.QtWidgets import QListWidget, QListWidgetItem

from app.layers.base_layer import Layer


class LayerPanel(QListWidget):
    def set_layers(self, layers: list[Layer]) -> None:
        self.clear()
        for layer in reversed(layers):
            item = QListWidgetItem(f"{'👁' if layer.visible else '🚫'} {layer.name} [{layer.blend_mode}] {int(layer.opacity * 100)}%")
            self.addItem(item)
