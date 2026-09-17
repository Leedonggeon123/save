"""프로젝트 화면에서 공통으로 사용하는 로그아웃 버튼입니다."""

from PySide6.QtWidgets import QPushButton


class LogoutButton(QPushButton):
    """크기와 색상이 통일된 로그아웃 버튼."""

    def __init__(self, parent=None):
        super().__init__("로그아웃", parent)
        self.setObjectName("logout")
        self.setFixedSize(160, 44)
        self.setStyleSheet(
            "QPushButton { background:#4295f4; color:white; border:0; "
            "border-radius:8px; font-size:14px; font-weight:600; padding:0; margin:0; }"
        )
