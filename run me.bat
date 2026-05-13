@echo off
setlocal

where python >nul 2>nul
if %errorlevel% neq 0 (
  echo Python not found in PATH.
  pause
  exit /b 1
)

python -c "import importlib.util,sys;mods=['PySide6','numpy','PIL'];missing=[m for m in mods if importlib.util.find_spec(m) is None];sys.exit(1 if missing else 0)"
if %errorlevel% neq 0 (
  echo Installing missing dependencies...
  python -m pip install PySide6 numpy pillow
  if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
  )
)

echo Launching BlendForge...
python launch_blendforge.py
if %errorlevel% neq 0 (
  echo BlendForge exited with an error.
  pause
  exit /b %errorlevel%
)

endlocal
