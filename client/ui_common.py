"""Shared paths and small UI helpers used by client screens."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SERVER_URL = os.getenv("JEWEL_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")


def logo_pixmap(path, width=72, height=72):
    """Make near-white pixels transparent and scale the Jewel logo."""
    image = QImage(str(path)).convertToFormat(QImage.Format_ARGB32)
    for y in range(image.height()):
        for x in range(image.width()):
            color = image.pixelColor(x, y)
            if color.red() > 245 and color.green() > 245 and color.blue() > 245:
                color.setAlpha(0)
                image.setPixelColor(x, y, color)
    return QPixmap.fromImage(image).scaled(
        width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )
