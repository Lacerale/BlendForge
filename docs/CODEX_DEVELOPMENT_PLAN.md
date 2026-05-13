# BlendForge Codex-Ready Development Plan

## Product Positioning
BlendForge is a **high-performance layer compositor** for blending/masking/effects workflows (not a full Photoshop clone).

### Target users
- Artists and texture artists
- VFX and compositing workflows
- Stylized lighting/shading (anime/manga, glow-heavy pipelines)

## v1 Scope (Non-destructive)
Each layer supports:
- Visibility/lock/reorder
- Opacity + blend mode
- Per-layer blur and adjustments
- Masks + selection-driven edits
- Transform metadata

Core principle: keep source pixels immutable until explicit flatten/export.

---

## Recommended Stack
- **UI:** PySide6/Qt (dockable desktop UI)
- **CPU rendering:** NumPy vectorized operations
- **Image ops:** OpenCV (blur, flood-fill, geometric transforms)
- **I/O:** Pillow (PNG/JPEG/BMP/WebP/TIFF), `psd-tools` (PSD import)
- **Acceleration roadmap:**
  - Phase 1: CPU + NumPy
  - Phase 2: OpenGL fragment shaders for blend/composite path

---

## Proposed Repository Layout
```text
BlendForge/
├── app/
│   ├── main.py
│   ├── ui/
│   ├── core/
│   ├── renderer/
│   ├── tools/
│   ├── layers/
│   ├── effects/
│   ├── selections/
│   ├── io/
│   ├── shaders/
│   └── utils/
└── docs/
```

### Core module responsibilities
- `ui/`: windowing, panels, canvas interactions
- `core/`: document lifecycle, history, commands, cache, settings
- `layers/`: layer types + layer manager
- `effects/`: blend modes, blur, color adjustments, masks
- `selections/`: lasso/polyline/wand/bucket and mask ops
- `renderer/`: compositing, tile rendering, GPU/preview/cache
- `io/`: imports/exports + internal project format

---

## Layer Data Model (Conceptual)
```python
class Layer:
    id: str
    name: str
    visible: bool
    locked: bool
    opacity: float
    blend_mode: str
    pixels: np.ndarray
    mask: np.ndarray | None

    blur_enabled: bool
    blur_type: str
    blur_radius: float
    blur_angle: float

    hue_shift: float
    saturation: float
    brightness: float
    contrast: float
    grayscale: bool
    invert: bool

    transform_matrix: np.ndarray
    cached_result: np.ndarray
    dirty: bool
```

---

## Blend Mode Roadmap
### Foundation
- Normal, Multiply, Screen, Overlay, Opacity

### Full target set
- Alpha Mask / Inverse Alpha Mask
- Darken, Multiply, Color Burn, Linear Burn
- Lighten, Screen, Color Dodge, Linear Dodge (Add)
- Glow, Soft Glow
- Overlay, Soft Light (Photoshop-style), Hard Light
- Hue, Saturation, Color, Luminosity
- Difference, Exclusion, Divide, Subtract
- Vivid Light, Pin Light, Hard Mix, Soft Mix

Implementation guidance:
- Use float32 in `[0, 1]`
- Clamp outputs after each mode
- Prefer vectorized NumPy (no per-pixel Python loops)

---

## Render Pipeline Order (per layer)
1. Source Pixels
2. Transform
3. Blur
4. Color Adjustments
5. Mask
6. Opacity
7. Blend Mode
8. Composite into canvas

This ordering keeps behavior predictable and non-destructive.

---

## Performance Strategy
- Dirty-layer invalidation + cached processed bitmaps
- Recompute changed layer and dependent layers only
- Tile rendering for large documents (e.g., 256×256 tiles)
- Low-res interactive preview; full-res export path
- Debounced slider updates and optional background workers

Target: responsive previews with a goal of 60 FPS around 2048×2048 scenes.

---

## Selection & Tooling Targets
- Lasso (freehand polygon)
- Polyline selection
- Magic Wand (`cv2.floodFill` + tolerance)
- Bucket fill
- Ops: Add/Subtract/Intersect/Invert/Feather/Expand/Contract

---

## File Support Plan
### Import
- PSD, TIFF, PNG, JPEG, BMP, WebP

### Export
- PNG, JPEG, BMP, WebP, TIFF

### Internal project format
- `.blendforge` (JSON metadata + compressed raster assets)
- Stores layers, masks, transforms, effects, visibility, adjustments

---

## Milestone Plan
1. **Foundation UI**: canvas, layer list, visibility toggle, basic open/save hooks
2. **Compositing engine**: Normal/Multiply/Screen/Overlay + opacity
3. **Advanced blend set**: remaining requested modes
4. **Effects**: Gaussian + directional blur, invert, hue/sat, grayscale
5. **Selections**: lasso/polyline/wand/bucket + selection ops
6. **GPU path**: shader-based compositing for real-time updates
7. **Polish**: shortcuts, thumbnails, presets, history/caching improvements

---

## Codex Tasking Strategy
Break work into subsystem-specific prompts. Example tasks:
- "Create a PySide6 layer panel widget with visibility, thumbnail, blend dropdown, opacity slider."
- "Implement NumPy blend operators for Multiply, Screen, Overlay, Soft Light, Hard Light."
- "Create OpenGL fragment shaders for Multiply, Screen, Color Dodge, Overlay."

Avoid broad prompts like "build Photoshop clone".
