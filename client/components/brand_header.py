"""공통 Jewel 브랜드 헤더."""
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from client.ui_common import PROJECT_ROOT, logo_pixmap


class BrandHeader(QWidget):
    """아이콘과 서비스명을 같은 규격으로 표시하는 공통 헤더."""

    ICON_SIZE = 84
    SPACING = 10

    def __init__(self, title="JEWEL", parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self.SPACING)

        icon = QLabel()
        icon.setPixmap(
            logo_pixmap(
                PROJECT_ROOT / "source" / "image" / "jewel_cloud_icon.png",
                self.ICON_SIZE,
                self.ICON_SIZE,
            )
        )
        layout.addWidget(icon)

        label = QLabel(title)
        label.setObjectName("brand")
        label.setStyleSheet(
            "color:#0b3d63; font-family:\"Ubuntu\"; font-size:32px; font-weight:800;"
        )
        layout.addWidget(label)
