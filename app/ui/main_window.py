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
from app.core.project_format import ProjectFormat
from app.effects.blend_modes import blend_mode_names
from app.io.image_io import save_image
from app.io.import_layers import import_layers_from_file
from app.tools.distortion_tool import DistortionMesh, warp_image_with_mesh
from app.ui.canvas_widget import CanvasWidget
from app.ui.directional_knob import DirectionalKnob
from app.ui.layer_panel import LayerPanel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BlendForge")
        self.resize(1360, 860)
        self.setMinimumSize(980, 620)

        self.document = Document()
        self.current_layer_index = -1
        self._base_distort_pixels = None
        self._refreshing = False

        root = QWidget()
        layout = QHBoxLayout(root)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.canvas = CanvasWidget()
        self.canvas.on_mesh_changed = self.preview_mesh_warp

        self.layer_panel = LayerPanel()
        self.layer_panel.visibilityChanged.connect(self.set_layer_visibility)
        self.layer_panel.opacityChanged.connect(self.set_layer_opacity)
        self.layer_panel.blendChanged.connect(self.set_layer_blend)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(self.canvas)

        right = QWidget()
        side = QVBoxLayout(right)

        open_btn = QPushButton("Open Layered File")
        open_btn.clicked.connect(self.open_image)
        export_btn = QPushButton("Export Composite")
        export_btn.clicked.connect(self.export_composite)
        save_proj_btn = QPushButton("Save .artproj")
        save_proj_btn.clicked.connect(self.save_project)
        open_proj_btn = QPushButton("Open .artproj")
        open_proj_btn.clicked.connect(self.open_project)


        select_none_btn = QPushButton("Selection: None")
        select_none_btn.clicked.connect(lambda: self.canvas.set_selection_mode("none"))
        lasso_btn = QPushButton("Lasso Tool")
        lasso_btn.clicked.connect(lambda: self.canvas.set_selection_mode("lasso"))
        poly_btn = QPushButton("Polyline Tool")
        poly_btn.clicked.connect(lambda: self.canvas.set_selection_mode("polyline"))
        wand_btn = QPushButton("Magic Wand")
        wand_btn.clicked.connect(lambda: self.canvas.set_selection_mode("wand"))
        self.blend_combo = QComboBox()
        self.blend_combo.addItems(blend_mode_names())
        self.blend_combo.currentTextChanged.connect(self.change_selected_blend)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.change_selected_opacity)

        self.blur_slider = QSlider(Qt.Orientation.Horizontal)
        self.blur_slider.setRange(0, 40)
        self.blur_slider.setValue(0)
        self.blur_slider.valueChanged.connect(self.change_selected_blur)

        self.distort_slider = QSlider(Qt.Orientation.Horizontal)
        self.distort_slider.setRange(0, 100)
        self.distort_slider.setValue(0)
        self.distort_slider.valueChanged.connect(self.change_selected_distortion)

        self.distort_toggle_btn = QPushButton("Toggle Distortion Tool (Commit on exit)")
        self.distort_toggle_btn.clicked.connect(self.toggle_distortion_mode)

        self.direction_knob = DirectionalKnob()
        self.direction_label = QLabel("Directional Blur Angle: 0°")
        self.direction_knob.angleChanged.connect(self.update_direction)

        self.boundary_width = QSpinBox()
        self.boundary_width.setRange(1, 20)
        self.boundary_width.setValue(2)
        boundary_btn = QPushButton("Create Boundary Layer")
        boundary_btn.clicked.connect(self.create_boundary)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter text")
        self.font_path: str | None = None
        font_btn = QPushButton("Upload Font")
        font_btn.clicked.connect(self.upload_font)
        text_btn = QPushButton("Add Text Layer")
        text_btn.clicked.connect(self.add_text_layer)

        for w in [
            open_btn, export_btn, save_proj_btn, open_proj_btn, select_none_btn, lasso_btn, poly_btn, wand_btn,
            QLabel("Blend Mode"), self.blend_combo,
            QLabel("Opacity"), self.opacity_slider,
            QLabel("Blur Intensity"), self.blur_slider,
            QLabel("Distortion Strength"), self.distort_slider, self.distort_toggle_btn,
            self.direction_label, self.direction_knob,
            QLabel("Boundary Width"), self.boundary_width, boundary_btn,
            self.text_input, font_btn, text_btn, self.layer_panel,
        ]:
            side.addWidget(w)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([1000, 360])
        layout.addWidget(splitter)
        self.setCentralWidget(root)
        self.statusBar().showMessage("Ready")

    def _selected_layer(self):
        layers = self.document.layer_manager.layers
        if not layers:
            return None
        if self.current_layer_index < 0:
            self.current_layer_index = len(layers) - 1
        self.current_layer_index = max(0, min(self.current_layer_index, len(layers) - 1))
        return layers[self.current_layer_index]

    def set_layer_visibility(self, layer_id: str, visible: bool) -> None:
        layer = self.document.layer_manager.get_layer(layer_id)
        if layer is None:
            return
        layer.visible = visible
        self.refresh_view()

    def set_layer_opacity(self, layer_id: str, opacity: float) -> None:
        layer = self.document.layer_manager.get_layer(layer_id)
        if layer is None:
            return
        layer.opacity = float(max(0.0, min(opacity, 1.0)))
        self.refresh_view()

    def set_layer_blend(self, layer_id: str, mode: str) -> None:
        layer = self.document.layer_manager.get_layer(layer_id)
        if layer is None:
            return
        layer.blend_mode = mode
        self.refresh_view()


    def save_project(self) -> None:
        if not self.document.layer_manager.layers:
            QMessageBox.information(self, "No layers", "Nothing to save.")
            return
        path = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if not path:
            return
        try:
            ProjectFormat.save(path, self.document.layer_manager.layers)
            self.statusBar().showMessage("Project saved", 4000)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to save project")
            QMessageBox.critical(self, "Save Error", str(exc))

    def open_project(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Open Project Folder")
        if not path:
            return
        try:
            layers = ProjectFormat.load(path)
            if not layers:
                raise RuntimeError("Project has no layers")
            self.document.layer_manager.layers = layers
            self.current_layer_index = len(layers) - 1
            self.refresh_view()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to open project")
            QMessageBox.critical(self, "Open Project Error", str(exc))

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Layered File",
            "",
            "Images (*.psd *.tif *.tiff *.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not path:
            return
        try:
            imported = import_layers_from_file(path)
            if not imported:
                raise RuntimeError("No layers found in file.")
            self.document.layer_manager.layers.clear()
            for name, image, visible in imported:
                layer = self.document.add_image_layer(image, name=name)
                layer.visible = visible
            self.current_layer_index = len(self.document.layer_manager.layers) - 1
            self.refresh_view()
            if path.lower().endswith((".tif", ".tiff")) and len(imported) == 1:
                self.statusBar().showMessage("TIFF opened with 1 layer (source may contain a single raster page).", 6000)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to open file")
            QMessageBox.critical(self, "Open Error", str(exc))

    def export_composite(self) -> None:
        pixels = self.document.render()
        if pixels is None:
            QMessageBox.information(self, "Nothing to export", "Load at least one layer first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Composite",
            "blendforge_export.png",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff)",
        )
        if not path:
            return
        try:
            save_image(path, pixels)
            self.statusBar().showMessage(f"Exported {Path(path).name}", 4000)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to export")
            QMessageBox.critical(self, "Export Error", str(exc))

    def create_boundary(self) -> None:
        layer = self.document.add_boundary_layer(self.boundary_width.value())
        if layer is None:
            QMessageBox.information(self, "No content", "Cannot create boundary without layers.")
            return
        self.current_layer_index = len(self.document.layer_manager.layers) - 1
        self.refresh_view()

    def upload_font(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Font", "", "Fonts (*.ttf *.otf)")
        if path:
            self.font_path = path
            self.statusBar().showMessage(f"Font loaded: {Path(path).name}")

    def add_text_layer(self) -> None:
        ref = self.document.render()
        if ref is None:
            QMessageBox.information(self, "Need base image", "Load at least one image layer first.")
            return
        self.document.add_text_layer(ref.shape, self.text_input.text(), self.font_path)
        self.current_layer_index = len(self.document.layer_manager.layers) - 1
        self.refresh_view()

    def change_selected_blend(self, mode: str) -> None:
        layer = self._selected_layer()
        if layer is None:
            return
        layer.blend_mode = mode
        self.refresh_view()

    def change_selected_opacity(self, value: int) -> None:
        layer = self._selected_layer()
        if layer is None:
            return
        layer.opacity = value / 100.0
        self.refresh_view()

    def change_selected_blur(self, value: int) -> None:
        layer = self._selected_layer()
        if layer is None:
            return
        layer.blur_radius = max(0, value)
        self.refresh_view()

    def change_selected_distortion(self, value: int) -> None:
        layer = self._selected_layer()
        if layer is None:
            return
        layer.distortion_strength = float(max(0, value))
        self.refresh_view()

    def update_direction(self, angle: float) -> None:
        layer = self._selected_layer()
        if layer is not None:
            layer.directional_blur_angle = angle
        self.direction_label.setText(f"Directional Blur Angle: {int(angle)}°")

    def toggle_distortion_mode(self) -> None:
        layer = self._selected_layer()
        if layer is None:
            return
        if not self.canvas.distortion_mode:
            self._base_distort_pixels = layer.pixels.copy()
            self.canvas.set_distortion_mode(True)
            self.statusBar().showMessage("Distortion mode enabled: drag mesh points")
            return

        if self.canvas.mesh is not None and self._base_distort_pixels is not None:
            layer.pixels = warp_image_with_mesh(self._base_distort_pixels, self.canvas.mesh)
        self.canvas.set_distortion_mode(False)
        self._base_distort_pixels = None
        self.statusBar().showMessage("Distortion committed")
        self.refresh_view()

    def preview_mesh_warp(self, mesh: DistortionMesh) -> None:
        layer = self._selected_layer()
        if layer is None or self._base_distort_pixels is None:
            return
        layer.pixels = warp_image_with_mesh(self._base_distort_pixels, mesh)
        self.refresh_view()

    def refresh_view(self) -> None:
        if self._refreshing:
            return
        self._refreshing = True
        try:
            pixels = self.document.render()
            self.canvas.set_pixels(pixels)
            self.layer_panel.set_layers(self.document.layer_manager.layers)
            self.statusBar().showMessage(f"Layers: {len(self.document.layer_manager.layers)}", 3000)
        finally:
            self._refreshing = False
