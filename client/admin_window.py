"""관리자 로그인 후 표시되는 관리자 전용 화면입니다."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from client.components.logout_button import LogoutButton


class AdminPage(QWidget):
    """관리자 메뉴와 회원 선택 영역을 표시하는 기본 관리자 화면입니다."""

    def __init__(self, logout):
        super().__init__()
        self.logout = logout
        self.setStyleSheet(
            "QWidget { background:white; }"
            "QWidget#sidebar { background:#e5f4fc; border-right:1px solid #444; }"
            "QLabel#brand { color:#0b3d63; font-size:28px; font-weight:800; }"
            "QPushButton#menu { background:transparent; color:#111; border:0;"
            "text-align:left; padding:10px 12px; font-size:15px; }"
            "QPushButton#menu:checked { color:#1877f2; font-weight:700; }"
            "QPushButton#action { background:#48aff0; color:white; border:0;"
            "border-radius:7px; padding:8px 18px; }"
        )

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(228)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(20, 18, 14, 20)

        brand = QLabel("Jewel")
        brand.setObjectName("brand")
        side.addWidget(brand)
        side.addSpacing(25)

        self.menu_buttons = []
        for title in ("차단", "차단 풀기", "공지", "회원등급"):
            button = QPushButton(title)
            button.setObjectName("menu")
            button.setCheckable(True)
            button.clicked.connect(lambda checked, name=title: self.select_menu(name))
            self.menu_buttons.append(button)
            side.addWidget(button)
        side.addStretch()
        outer.addWidget(sidebar)

        content = QVBoxLayout()
        content.setContentsMargins(28, 18, 28, 28)

        header = QHBoxLayout()
        header.addStretch()
        logout_button = LogoutButton()
        logout_button.clicked.connect(self.logout)
        header.addWidget(logout_button)
        content.addLayout(header)

        title = QLabel("아이디 목록")
        title.setStyleSheet("font-size:16px; font-weight:600;")
        content.addWidget(title)

        list_box = QWidget()
        list_box.setStyleSheet("border:1px solid #222;")
        list_layout = QVBoxLayout(list_box)
        list_layout.setContentsMargins(16, 16, 16, 16)
        list_layout.setSpacing(14)

        # 실제 회원 목록 API 연결 전까지는 화면 구조 확인용 선택 행을 표시합니다.
        for index in range(1, 16):
            checkbox = QCheckBox(f"회원 {index}")
            checkbox.setStyleSheet("border:0;")
            list_layout.addWidget(checkbox)
        list_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(list_box)
        scroll.setMinimumHeight(500)
        content.addWidget(scroll)

        action = QPushButton("차단하기")
        action.setObjectName("action")
        action.clicked.connect(self.block_selected)
        content.addWidget(action, alignment=Qt.AlignCenter)
        outer.addLayout(content, 1)

        self.select_menu("차단")

    def select_menu(self, name):
        """왼쪽 관리자 카테고리의 선택 상태를 바꿉니다."""
        for button in self.menu_buttons:
            button.setChecked(button.text() == name)
        print(f"관리자 메뉴 선택: {name}", flush=True)

    def block_selected(self):
        """선택된 회원 차단 API를 연결하기 전 안내 팝업을 표시합니다."""
        QMessageBox.information(
            self,
            "관리자 기능",
            "회원 차단 기능은 관리자 API 연결 후 사용할 수 있습니다.",
        )


__all__ = ["AdminPage"]


# 관리자 화면만 단독으로 UI를 확인할 때 사용하는 테스트 진입점입니다.
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = AdminPage(lambda: window.close())
    window.setWindowTitle("JEWEL Cloud - 관리자")
    window.resize(1280, 800)
    window.show()
    sys.exit(app.exec())
