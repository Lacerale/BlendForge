# BlendForge

BlendForge is a robust, dark-themed desktop prototype for real-time layer compositing.

## Features in this build
- High-quality dark adaptive UI
- Resizable splitter-based layout for progressive workspace scaling
- Circular directional control knob with arrow for directional blur angle input
- Multi-layer compositing engine (NumPy)
- Extended blend modes: normal, darken, lighten, multiply, screen, overlay, hard/soft light, color dodge/burn, linear dodge/burn, difference, exclusion
- Layer visibility toggling, blend mode and opacity controls
- Import image as a layer + export flattened composite
- Startup/runtime logging (`logs/blendforge.log`)

## One-click run (Windows)
Double-click `run me.bat` or run:

```bat
run me.bat
```

The script installs missing dependencies if needed, then launches the app.

## Manual run
```bash
pip install PySide6 numpy pillow
python launch_blendforge.py
```
