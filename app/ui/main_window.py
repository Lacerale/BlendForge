from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QSlider,
    QSpinBox,
)

from app.core.document import Document
from app.effects.blend_modes import blend_mode_names
from app.io.image_io import load_image, save_image
from app.ui.canvas_widget import CanvasWidget
from app.ui.directional_knob import DirectionalKnob
from app.ui.layer_panel import LayerPanel
from app.tools.distortion_tool import warp_image_with_mesh

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BlendForge")
        self.resize(1360, 860)
        self.setMinimumSize(980, 620)
        self.document = Document()
        self.current_layer_index = -1

        root = QWidget()
        layout = QHBoxLayout(root)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.canvas = CanvasWidget()
        self.canvas.on_mesh_changed = self.preview_mesh_warp
        self._base_distort_pixels = None
        self.layer_panel = LayerPanel()

        left = QWidget(); left_layout = QVBoxLayout(left); left_layout.addWidget(self.canvas)
        right = QWidget(); side = QVBoxLayout(right)

        open_btn = QPushButton("Open Image as Layer"); open_btn.clicked.connect(self.open_image)
        export_btn = QPushButton("Export Composite"); export_btn.clicked.connect(self.export_composite)
        next_btn = QPushButton("Select Next Layer"); next_btn.clicked.connect(self.select_next_layer)
        hide_btn = QPushButton("Hide/View Selected Layer"); hide_btn.clicked.connect(self.toggle_selected_layer)

        self.blend_combo = QComboBox(); self.blend_combo.addItems(blend_mode_names()); self.blend_combo.currentTextChanged.connect(self.change_selected_blend)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal); self.opacity_slider.setRange(0,100); self.opacity_slider.setValue(100); self.opacity_slider.valueChanged.connect(self.change_selected_opacity)
        self.blur_slider = QSlider(Qt.Orientation.Horizontal); self.blur_slider.setRange(0,40); self.blur_slider.setValue(0); self.blur_slider.valueChanged.connect(self.change_selected_blur)
        self.distort_slider = QSlider(Qt.Orientation.Horizontal); self.distort_slider.setRange(0,100); self.distort_slider.setValue(0); self.distort_slider.valueChanged.connect(self.change_selected_distortion)
        self.distort_toggle_btn = QPushButton("Toggle Distortion Tool (Commit on exit)"); self.distort_toggle_btn.clicked.connect(self.toggle_distortion_mode)

        self.direction_knob = DirectionalKnob(); self.direction_label = QLabel("Directional Blur Angle: 0°"); self.direction_knob.angleChanged.connect(self.update_direction)

        self.boundary_width = QSpinBox(); self.boundary_width.setRange(1, 20); self.boundary_width.setValue(2)
        boundary_btn = QPushButton("Create Boundary Layer"); boundary_btn.clicked.connect(self.create_boundary)

        self.text_input = QLineEdit(); self.text_input.setPlaceholderText("Enter text")
        self.font_path: str | None = None
        font_btn = QPushButton("Upload Font"); font_btn.clicked.connect(self.upload_font)
        text_btn = QPushButton("Add Text Layer"); text_btn.clicked.connect(self.add_text_layer)

        for w in [open_btn, export_btn, next_btn, hide_btn, QLabel("Blend Mode"), self.blend_combo,
                  QLabel("Opacity"), self.opacity_slider, QLabel("Blur Intensity"), self.blur_slider,
                  QLabel("Distortion Strength"), self.distort_slider, self.distort_toggle_btn,
                  self.direction_label, self.direction_knob,
                  QLabel("Boundary Width"), self.boundary_width, boundary_btn,
                  self.text_input, font_btn, text_btn, self.layer_panel]:
            side.addWidget(w)

        splitter.addWidget(left); splitter.addWidget(right); splitter.setSizes([1000, 360]); layout.addWidget(splitter)
        self.setCentralWidget(root); self.statusBar().showMessage("Ready")

    def _selected_layer(self):
        layers = self.document.layer_manager.layers
        if not layers: return None
        if self.current_layer_index < 0: self.current_layer_index = len(layers)-1
        self.current_layer_index %= len(layers)
        return layers[self.current_layer_index]

    def select_next_layer(self):
        if self.document.layer_manager.layers:
            self.current_layer_index = (self.current_layer_index + 1) % len(self.document.layer_manager.layers)
            layer = self._selected_layer(); self.statusBar().showMessage(f"Selected: {layer.name}")

    def toggle_selected_layer(self):
        layer = self._selected_layer()
        if layer: self.document.toggle_visibility(layer.id); self.refresh_view()

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff)")
        if not path: return
        try:
            image = load_image(path); self.document.add_image_layer(image, name=Path(path).name); self.current_layer_index = len(self.document.layer_manager.layers)-1; self.refresh_view()
        except Exception as exc: logger.exception("Failed to load image"); QMessageBox.critical(self, "Open Error", str(exc))

    def export_composite(self) -> None:
        pixels = self.document.render()
        if pixels is None: QMessageBox.information(self, "Nothing to export", "Load at least one layer first."); return
        path, _ = QFileDialog.getSaveFileName(self, "Export Composite", "blendforge_export.png", "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff)")
        if not path: return
        try: save_image(path, pixels); self.statusBar().showMessage(f"Exported {Path(path).name}", 4000)
        except Exception as exc: logger.exception("Failed to export"); QMessageBox.critical(self, "Export Error", str(exc))

    def create_boundary(self):
        self.document.add_boundary_layer(self.boundary_width.value()); self.refresh_view()

    def upload_font(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Font", "", "Fonts (*.ttf *.otf)")
        if path: self.font_path = path; self.statusBar().showMessage(f"Font loaded: {Path(path).name}")

    def add_text_layer(self):
        ref = self.document.render()
        if ref is None: QMessageBox.information(self, "Need base image", "Load at least one image layer first."); return
        self.document.add_text_layer(ref.shape, self.text_input.text(), self.font_path); self.refresh_view()

    def change_selected_blend(self, mode: str):
        layer = self._selected_layer();
        if layer: layer.blend_mode = mode; self.refresh_view()

    def change_selected_opacity(self, value: int):
        layer = self._selected_layer();
        if layer: layer.opacity = value / 100.0; self.refresh_view()

    def change_selected_blur(self, value: int):
        layer = self._selected_layer();
        if layer: layer.blur_radius = value; self.refresh_view()

    def change_selected_distortion(self, value: int):
        layer = self._selected_layer();
        if layer: layer.distortion_strength = float(value); self.refresh_view()

    def update_direction(self, angle: float):
        layer = self._selected_layer()
        if layer: layer.directional_blur_angle = angle
        self.direction_label.setText(f"Directional Blur Angle: {int(angle)}°")


    def toggle_distortion_mode(self):
        layer = self._selected_layer()
        if layer is None:
            return
        if not self.canvas.distortion_mode:
            self._base_distort_pixels = layer.pixels.copy()
            self.canvas.set_distortion_mode(True)
            self.statusBar().showMessage("Distortion mode enabled: drag mesh points")
        else:
            if self.canvas.mesh is not None and self._base_distort_pixels is not None:
                layer.pixels = warp_image_with_mesh(self._base_distort_pixels, self.canvas.mesh)
            self.canvas.set_distortion_mode(False)
            self._base_distort_pixels = None
            self.statusBar().showMessage("Distortion committed")
            self.refresh_view()

    def preview_mesh_warp(self, mesh):
        layer = self._selected_layer()
        if layer is None or self._base_distort_pixels is None:
            return
        layer.pixels = warp_image_with_mesh(self._base_distort_pixels, mesh)
        self.refresh_view()
    def refresh_view(self) -> None:
        pixels = self.document.render(); self.canvas.set_pixels(pixels); self.layer_panel.set_layers(self.document.layer_manager.layers)
        self.statusBar().showMessage(f"Layers: {len(self.document.layer_manager.layers)}", 3000)
