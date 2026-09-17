"""Main dashboard screen shown after a successful login."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

                                         
from client.ui_common import PROJECT_ROOT, logo_pixmap

# 로그인 성공 후 보이는 메인 메뉴 화면
class DashboardPage(QWidget):
    """로그인 성공 후 표시할 Jewel Cloud 메인 화면

    현재는 UI만 먼저 만들고, 버튼 기능은 콘솔 출력으로 대체
    메일/파일/설정 화면을 만들면 각 메서드에 연결
    """

    # logout은 로그아웃 전환 함수, show_settings는 설정 화면 전환 함수
    def __init__(self, logout, show_settings, show_file, show_mail=None):
        super().__init__()
        
        self.logout = logout
        self.show_settings = show_settings
        self.show_file = show_file                                                                              # 파일 버튼 클릭했을떄 실행할 함수를 저장
        self.show_mail = show_mail
        self.setStyleSheet(
            "QWidget { background: white; }"
            "QLabel#brand { color:#0b3d63; font-size:28px; font-weight:800; }"
            "QPushButton { background:#2379aa; color:white; border:0;"
            "border-radius:8px; font-size:16px; font-weight:600; }"
            "QPushButton:hover { background:#1d6d9c; }"
        )

        # 로고, 중앙메뉴 배치
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 24)
        root.setSpacing(0)

        # 로고, 서비스 이름
        header = QHBoxLayout()
        icon = QLabel()
        icon_path = PROJECT_ROOT / "mail" / "mail_client" / "assets" / "jewel_cloud_logo.png"
        icon.setPixmap(logo_pixmap(icon_path))
        header.addWidget(icon)
        brand = QLabel("JEWEL")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch()
        root.addLayout(header)
        root.addStretch(1)

        # 메일·파일·설정 버튼 가로 중앙에 배치
        menu = QHBoxLayout()
        menu.setContentsMargins(0, 0, 0, 0)
        menu.setSpacing(152)
        menu.setAlignment(Qt.AlignCenter)
        for label, handler in (
            ("메일", self.open_mail),
            ("파일", self.open_file),
            ("설정", self.open_settings),
        ):
            button = QPushButton(label)
            button.setFixedSize(150, 140)
            button.clicked.connect(handler)
            menu.addWidget(button)
        root.addLayout(menu)
        root.addStretch(1)
        # 설정 화면의 뒤로가기 버튼과 같은 높이를 예약해
        # 두 화면의 중앙 버튼 위치가 같아지도록
        bottom_space = QWidget()
        bottom_space.setFixedHeight(38)
        bottom_space.setStyleSheet("background: transparent;")
        root.addWidget(bottom_space)

    # 현재 메일 화면에 연결된 것 없음. 클릭 로그만 출력
    def open_mail(self):
        if self.show_mail:
            self.show_mail()

    # 현재 파일 화면에 연결된 것 없음. 클릭 로그만 출력
    def open_file(self):
        self.show_file()

    # 설정 버튼은 JewelClient의 설정 화면 전환 콜백을 호출
    def open_settings(self):
        self.show_settings()


__all__ = ["DashboardPage"]
