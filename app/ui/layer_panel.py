from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QFrame,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QSlider,
    QComboBox,
)

from app.effects.blend_modes import blend_mode_names
from app.layers.base_layer import Layer


class LayerRow(QFrame):
    visibilityChanged = Signal(str, bool)
    opacityChanged = Signal(str, float)
    blendChanged = Signal(str, str)

    def __init__(self, layer: Layer) -> None:
        super().__init__()
        self.layer = layer
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self.vis = QCheckBox()
        self.vis.setChecked(layer.visible)
        self.vis.toggled.connect(lambda v: self.visibilityChanged.emit(layer.id, v))
        self.label = QLabel(layer.name)
        top.addWidget(self.vis)
        top.addWidget(self.label)
        layout.addLayout(top)

        self.blend = QComboBox()
        self.blend.addItems(blend_mode_names())
        self.blend.setCurrentText(layer.blend_mode)
        self.blend.currentTextChanged.connect(lambda m: self.blendChanged.emit(layer.id, m))
        layout.addWidget(self.blend)

        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(0, 100)
        self.opacity.setValue(int(layer.opacity * 100))
        self.opacity.valueChanged.connect(lambda v: self.opacityChanged.emit(layer.id, v / 100.0))
        layout.addWidget(self.opacity)


class LayerPanel(QWidget):
    visibilityChanged = Signal(str, bool)
    opacityChanged = Signal(str, float)
    blendChanged = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.outer = QVBoxLayout(self)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.addStretch(1)
        self.scroll.setWidget(self.content)
        self.outer.addWidget(self.scroll)

    def set_layers(self, layers: list[Layer]) -> None:
        for i in reversed(range(self.content_layout.count() - 1)):
            item = self.content_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        for layer in reversed(layers):
            row = LayerRow(layer)
            row.visibilityChanged.connect(self.visibilityChanged)
            row.opacityChanged.connect(self.opacityChanged)
            row.blendChanged.connect(self.blendChanged)
            self.content_layout.insertWidget(self.content_layout.count() - 1, row)
