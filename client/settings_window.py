"""설정 화면"""
from __future__ import annotations

import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFormLayout,QHBoxLayout,QLabel,QMessageBox,QPushButton,QLineEdit,QStackedWidget,QVBoxLayout,QWidget,)

from client.components.logout_button import LogoutButton
from client.components.back_button import BackButton
from client.components.upgrade_button import UpgradeButton
from client.components.brand_header import BrandHeader
from client.ui_common import SERVER_URL
from client.session import UserSession

# 설정 메뉴에서 개인·메일·파일 설정으로 이동하는 화면
class SettingsPage(QWidget):
    """설정 메뉴 화면"""

    # go_back은 메인 화면, logout은 로그인 화면, show_personal은 개인설정으로 연결
    def __init__(self, go_back, logout, show_personal, show_file_settings):
        super().__init__()
        self.go_back = go_back
        self.logout = logout
        self.show_personal = show_personal
        
        self.show_file_settings = show_file_settings                    # 파일 설정 버튼을 클릭했을떄
        
        self.setStyleSheet(
            "QWidget { background: white; }"
            "QLabel#brand { color:#0b3d63; font-size:32px; font-weight:800; }"
            "QPushButton { background:#2379aa; color:white; border:0;"
            "border-radius:8px; font-size:16px; font-weight:600; }"
            "QPushButton#logout,QPushButton#back { background:#4295f4; }"
        )

        # 상단 헤더, 중앙 설정 버튼, 하단 뒤로가기 버튼을 세로로 배치
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 20)
        root.setSpacing(0)

        header = QHBoxLayout()
        header.addWidget(BrandHeader("JEWEL"))
        header.addStretch()
        logout_button = LogoutButton()
        logout_button.clicked.connect(self.logout)
        header.addWidget(logout_button)
        root.addLayout(header)
        root.addStretch(1)

        menu = QHBoxLayout()
        menu.setSpacing(152)
        menu.setAlignment(Qt.AlignCenter)
        for label, handler in (
            ("개인설정", self.open_account),
            ("메일설정", self.open_mail),
            ("파일설정", self.open_file),
        ):
            button = QPushButton(label)
            button.setFixedSize(150, 140)
            button.clicked.connect(handler)
            menu.addWidget(button)
        root.addLayout(menu)
        root.addStretch(1)
        back_button = BackButton()
        back_button.clicked.connect(self.go_back)
        root.addWidget(back_button, alignment=Qt.AlignLeft | Qt.AlignBottom)

    # 개인설정 상세 페이지로 이동
    def open_account(self):
        print("개인설정 버튼 클릭", flush=True)
        self.show_personal()

    # 메일 설정. 연결 안 됨
    def open_mail(self):
        print("메일설정 버튼 클릭", flush=True)

    # 파일 설정. 연결 안 됨
    def open_file(self):
        self.show_file_settings()                                                               # 파일 설정 호출            


# 왼쪽 카테고리와 오른쪽 상세 페이지를 함께 관리하는 개인설정 화면
class PersonalSettingsPage(QWidget):
    """개인설정의 왼쪽 카테고리와 오른쪽 내용 영역"""

    # go_back은 설정 메뉴, logout은 로그인 화면으로 돌아가는 콜백
    def __init__(self, go_back, logout, session=None):
        super().__init__()
        self.go_back = go_back
        self.logout = logout
        self.session = session or UserSession()
        self.setStyleSheet(
            "QWidget { background:white; }"
            "QWidget#sidebar { background:#e5f4fc; border-right:1px solid #444; }"
            "QLabel#brand { color:#0b3d63; font-size:28px; font-weight:800; }"
            "QPushButton#category { background:transparent; color:#111; border:0;"
            "text-align:left; padding:10px 12px; font-size:15px; }"
            "QPushButton#category:checked { color:#1877f2; font-weight:700; }"
            "QPushButton#logout { background:#4295f4; color:white; border:0;"
            "border-radius:8px; font-size:14px; }"
            "QPushButton#back { background:#4295f4; color:white; border:0;"
            "border-radius:6px; font-size:13px; }"
            "QPushButton#upgrade { background:#176a99; color:white; border:0;"
            "border-radius:7px; padding:8px 18px; min-width:72px; min-height:32px; }"
            "QLineEdit { background:#eeeeee; border:0; border-radius:7px;"
            "padding:12px 16px; font-size:16px; }"
        )

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(228)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(24, 18, 14, 20)
        side.setSpacing(8)
        side.addWidget(BrandHeader("Jewel"))
        side.addSpacing(18)

        self.category_buttons = []
        for text, index in (
            ("서비스 확인 및 변경", 0),
            ("기본 이메일", 1),
            ("개인 정보", 2),
        ):
            button = QPushButton(text)
            button.setObjectName("category")
            button.setCheckable(True)
            button.clicked.connect(lambda checked, i=index: self.select_category(i))
            self.category_buttons.append(button)
            side.addWidget(button)
        side.addStretch()
        back_button = BackButton()
        back_button.clicked.connect(self.go_back)
        side.addWidget(back_button, alignment=Qt.AlignLeft)
        # side는 레이아웃이므로, 실제 위젯인 sidebar를 바깥 레이아웃에 추가
        outer.addWidget(sidebar)

        content = QVBoxLayout()
        content.setContentsMargins(28, 18, 24, 28)
        content.setSpacing(0)
        header = QHBoxLayout()
        header.addStretch()
        # 개인설정 상세 화면에서는 사이드바의 뒤로가기로 이동합니다.
        content.addLayout(header)

        # 세 가지 개인설정 콘텐츠를 하나씩 보여주는 스택 위젯
        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_service_page())
        self.pages.addWidget(self.create_email_page())
        self.pages.addWidget(self.create_personal_info_page())
        content.addWidget(self.pages)
        outer.addLayout(content, 1)

        self.select_category(0)

    # 왼쪽 메뉴 번호에 맞춰 오른쪽 콘텐츠 페이지 선택
    def select_category(self, index):
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.category_buttons):
            button.setChecked(i == index)

    # 등급 카드
    def create_service_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 8, 16, 0)
        title = QLabel("내 등급: 일반")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:24px; font-weight:700;")
        layout.addWidget(title)
        layout.addSpacing(72)

        cards = QHBoxLayout()
        cards.setSpacing(24)
        cards.setAlignment(Qt.AlignCenter)
        plans = (
            ("일반", "파일 업로드 용량\n100MB", "무료", "사용 중", True),
            ("비즈니스", "파일 업로드 용량\n200MB", "월 30,000원", "업그레이드", False),
            ("VIP", "파일 업로드 용량\n500MB", "월 120,000원", "업그레이드", False),
            ("VVIP", "파일 업로드 용량\n1GB", "월 200,000원", "업그레이드", False),
        )
        colors = ("#e5f4fc", "#48aff0", "#2379aa", "#0b3d63")
        for card_index, ((name, capacity, price, action, current), color) in enumerate(zip(plans, colors)):
            card = QVBoxLayout()
            card.setContentsMargins(20, 20, 20, 40)
            card.setSpacing(12)
            panel = QWidget()
            panel.setFixedSize(200, 500)
            panel.setStyleSheet(f"background:{color}; border-radius:15px;")
            panel.setLayout(card)
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignCenter)
            text_color = "#ffffff" if card_index in (2, 3) else "#111111"
            name_label.setStyleSheet(
                f"font-size:18px; font-weight:700; color:{text_color};"
            )
            card.addWidget(name_label)
            card.addStretch()
            info = QLabel(capacity)
            info.setAlignment(Qt.AlignCenter)
            info.setStyleSheet(f"font-size:15px; color:{text_color};")
            card.addWidget(info)
            price_label = QLabel(price)
            price_label.setAlignment(Qt.AlignCenter)
            price_label.setStyleSheet(f"color:{text_color};")
            card.addWidget(price_label)
            card.addStretch()
            # 모든 카드의 하단 동작 영역 높이를 같게 유지
            action_area = QWidget()
            action_area.setFixedHeight(46)
            action_layout = QHBoxLayout(action_area)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setAlignment(Qt.AlignCenter)
            if current:
                current_label = QLabel("사용 중")
                current_label.setAlignment(Qt.AlignCenter)
                current_label.setStyleSheet("color:#8a8a8a; font-size:14px;")
                action_layout.addWidget(current_label)
            else:
                button_color = ("#176a99" if card_index == 1 else
                                "#0b3d63" if card_index == 2 else
                                "#2379aa")
                action_button = UpgradeButton(button_color)
                action_button.clicked.connect(self.show_upgrade_message)
                action_layout.addWidget(action_button)
            card.addWidget(action_area)
            cards.addWidget(panel)
        layout.addLayout(cards)
        layout.addStretch()
        return page

    # 기본 발신 이메일 입력 UI를 만드는 함수
    def create_email_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        row_box = QWidget()
        row_box.setFixedWidth(560)
        row = QHBoxLayout(row_box)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        row.addWidget(QLabel("보내는 사람"))
        self.sender_email_input = QLineEdit("jewel@gmail.com")
        self.sender_email_input.setFixedWidth(430)
        self.sender_email_input.setFixedHeight(48)
        # 저장 버튼 없이 입력 완료(Enter 또는 포커스 이동)를 감지
        self.sender_email_input.editingFinished.connect(self.save_default_email)
        row.addWidget(self.sender_email_input)
        layout.addWidget(row_box, alignment=Qt.AlignCenter)
        return page

    # 입력 완료 시 USER_SETTINGS.default_sender_email을 서버에 저장
    def save_default_email(self):
        """USER_SETTINGS.default_sender_email을 자동으로 수정"""
        if not self.session.user_id:
            print("기본 이메일 저장 대기: 로그인 사용자 정보가 없습니다.", flush=True)
            return
        email = self.sender_email_input.text().strip()
        try:
            response = requests.put(
                f"{SERVER_URL}/api/settings/default-sender-email",
                json={"user_id": self.session.user_id, "default_sender_email": email},
                timeout=10,
            )
            if response.ok:
                print("USER_SETTINGS.default_sender_email 저장 완료", flush=True)
            else:
                QMessageBox.warning(self, "저장 실패", response.json().get("detail", "기본 이메일을 저장할 수 없습니다."))
        except requests.RequestException:
            QMessageBox.warning(self, "연결 오류", "서버에 연결할 수 없습니다.")

    # 개인설정 진입 시 로그인한 사용자의 기본 이메일을 서버에서 불러옴
    def load_default_email(self):
        """개인설정 화면을 열 때 DB에 저장된 기본 이메일을 불러옴"""
        if not self.session.user_id:
            return
        try:
            response = requests.get(
                f"{SERVER_URL}/api/settings/default-sender-email/{self.session.user_id}",
                timeout=10,
            )
            if response.ok:
                self.sender_email_input.setText(response.json().get("default_sender_email", ""))
        except requests.RequestException:
            print("기본 이메일을 불러오지 못했습니다.", flush=True)

    # 이름·읽기 전용 이메일·비밀번호 수정 UI
    def create_personal_info_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 90, 60, 60)
        title = QLabel("개인 정보")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:30px; font-weight:800; color:#111;")
        layout.addWidget(title)
        layout.addSpacing(54)

        form_box = QWidget()
        form_box.setMaximumWidth(600)
        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        form.setContentsMargins(0, 0, 0, 0)

        self.name_input = QLineEdit("")
        self.email_input = QLineEdit("")
        name_input = self.name_input
        email_input = self.email_input
        email_input.setReadOnly(True)
        email_input.setStyleSheet("color:#777; background:#eeeeee;")
        self.password_input = QLineEdit()
        password_input = self.password_input
        password_input.setEchoMode(QLineEdit.Password)
        password_input.setPlaceholderText("●●●●●●●●●●")
        self.password_confirm_input = QLineEdit()
        password_confirm_input = self.password_confirm_input
        password_confirm_input.setEchoMode(QLineEdit.Password)
        password_confirm_input.setPlaceholderText("●●●●●●●●●●")
        for field in (name_input, email_input, password_input, password_confirm_input):
            field.setFixedHeight(48)
            field.setFixedWidth(500)
        form.addRow("이름", name_input)
        form.addRow("구글 이메일", email_input)
        form.addRow("비밀번호", password_input)
        form.addRow("비밀번호 확인", password_confirm_input)
        form_box.setLayout(form)
        layout.addWidget(form_box, alignment=Qt.AlignHCenter)
        layout.addStretch()
        button = QPushButton("정보수정")
        button.setObjectName("upgrade")
        button.clicked.connect(self.update_profile)
        layout.addWidget(button, alignment=Qt.AlignCenter)
        return page

    # 이름만 또는 이름과 새 비밀번호를 검증한 뒤 서버에 저장
    def update_profile(self):
        """이름과 새 비밀번호를 검사한 뒤 서버에 저장"""
        name = self.name_input.text().strip()
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()
        if not name:
            QMessageBox.warning(self, "입력 오류", "이름을 입력해주세요.")
            return
        if bool(password) != bool(password_confirm):
            QMessageBox.warning(self, "입력 오류", "비밀번호와 비밀번호 확인을 모두 입력해주세요.")
            return
        if password and len(password) < 10:
            QMessageBox.warning(self, "입력 오류", "비밀번호는 10자리 이상이어야 합니다.")
            return
        if password and password != password_confirm:
            QMessageBox.warning(self, "입력 오류", "비밀번호가 서로 일치하지 않습니다.")
            return
        if not self.session.user_id:
            QMessageBox.warning(self, "저장 실패", "로그인 사용자 정보를 확인할 수 없습니다.")
            return
        try:
            response = requests.put(
                f"{SERVER_URL}/api/settings/profile",
                json={"user_id": self.session.user_id, "name": name, **({"password": password} if password else {})},
                timeout=10,
            )
            if response.ok:
                QMessageBox.information(self, "수정 완료", "개인정보가 수정되었습니다.")
                self.session.name = name
                self.password_input.clear()
                self.password_confirm_input.clear()
            else:
                detail = response.json().get("detail", "개인정보를 수정할 수 없습니다.")
                if isinstance(detail, list):
                    detail = "\n".join(item.get("msg", "입력값을 확인해주세요.") for item in detail)
                QMessageBox.warning(self, "수정 실패", str(detail))
        except requests.RequestException:
            QMessageBox.warning(self, "연결 오류", "서버에 연결할 수 없습니다.")

    # 페이지를 다시 열 때 비밀번호 입력칸 초기화
    def reset_form(self):
        """개인정보 화면을 다시 열 때 비밀번호 입력값을 초기화합니다."""
        self.password_input.clear()
        self.password_confirm_input.clear()
        self.password_input.setPlaceholderText("●●●●●●●●●●")
        self.password_confirm_input.setPlaceholderText("●●●●●●●●●●")

    # 로그아웃 시 개인정보 화면의 사용자 입력 모두 초기화
    def reset_all_form(self):
        """로그아웃 시 개인정보 입력 폼 전체를 비웁니다."""
        self.name_input.clear()
        self.email_input.clear()
        self.reset_form()

    # 로그인 응답으로 받은 현재 사용자 정보를 화면에 표시
    def set_user_info(self, name, email):
        """로그인한 사용자 정보를 개인정보 화면에 표시합니다."""
        self.name_input.setText(name or "")
        self.email_input.setText(email or "")

    # 실제 관리자 등급 변경 전까지 안내 팝업만 표시
    def show_upgrade_message(self):
        QMessageBox.information(self, "등급 업그레이드", "변경 불가\n관리자에게 문의하세요.")

# 아래 두 클래스만 넘김 / 코드 충돌 방지
__all__ = ["SettingsPage", "PersonalSettingsPage"]
