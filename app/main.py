from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from app.ui.main_window import MainWindow
from app.ui.theme import DARK_STYLESHEET


def _configure_logging() -> None:
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.FileHandler("logs/blendforge.log"), logging.StreamHandler(sys.stdout)],
    )


def main() -> int:
    _configure_logging()
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    try:
        window = MainWindow()
        window.show()
        return app.exec()
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(None, "BlendForge Startup Error", str(exc))
        logging.exception("Startup error")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
