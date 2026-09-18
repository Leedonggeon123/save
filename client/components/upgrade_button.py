"""등급 카드에서 공통으로 사용하는 업그레이드 버튼입니다."""

from PySide6.QtWidgets import QPushButton


class UpgradeButton(QPushButton):
    """크기와 모양이 항상 같은 업그레이드 버튼."""

    def __init__(self, background_color: str, parent=None):
        super().__init__("업그레이드", parent)
        self.setFixedSize(92, 38)
        self.setStyleSheet(
            f"QPushButton {{ background:{background_color}; color:white; "
            "border:0; border-radius:7px; font-size:13px; "
            "padding:0; margin:0; }"
        )
