"""설정 화면에서 공통으로 사용하는 뒤로가기 버튼."""

from PySide6.QtWidgets import QPushButton


class BackButton(QPushButton):
    """크기와 글꼴이 통일된 뒤로가기 버튼."""

    def __init__(self, parent=None):
        super().__init__("뒤로가기", parent)
        self.setObjectName("back")
        self.setFixedSize(100, 38)
        self.setStyleSheet(
            "QPushButton { background:#4295f4; color:white; border:0; "
            "border-radius:6px; font-size:14px; font-weight:600; "
            "padding:0; margin:0; }"
        )
