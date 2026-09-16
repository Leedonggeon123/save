# -*- coding: utf-8 -*-
"""관리자 화면의 고정 UI 구성 모듈."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QTableWidget, QVBoxLayout, QWidget, QTextEdit, QMessageBox, QDialog
)
from client.components.logout_button import LogoutButton


class NoticeConfirmDialog(QDialog):
    """공지 전송 전 확인 다이얼로그 (회원님 UI 디자인/좌표 기준)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
        self.setMaximumSize(800, 600)
        self.setWindowTitle("Jewel")
        self.setStyleSheet('QDialog { background: #f7f7f7; } QPushButton#confirmButton, QPushButton#cancelButton { background: #49adf0; border: none; border-radius: 8px; font: 14px "Malgun Gothic"; color: #000; }')
        
        self.messageLabel = QLabel("공지(모두에게 보내기)\n하시겠습니까?", self)
        self.messageLabel.setGeometry(180, 244, 440, 100)
        self.messageLabel.setAlignment(Qt.AlignCenter)
        self.messageLabel.setStyleSheet('font: 700 40px "Malgun Gothic"; color: #000;')

        self.confirmButton = QPushButton("확인", self)
        self.confirmButton.setObjectName("confirmButton")
        self.confirmButton.setGeometry(303, 488, 80, 37)
        self.confirmButton.clicked.connect(self.accept)
        
        self.cancelButton = QPushButton("취소", self)
        self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.setGeometry(420, 488, 80, 37)
        self.cancelButton.clicked.connect(self.reject)


class NoticeCompleteDialog(QDialog):
    """공지 전송 완료 다이얼로그 (회원님 UI 디자인/좌표 기준)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(400, 300)
        self.setMinimumSize(400, 300)
        self.setMaximumSize(400, 300)
        self.setWindowTitle("Jewel")
        self.setStyleSheet("QDialog { background: #6d7582; }")

        self.completeLabel = QLabel("공지(모두에게 보내기)\n되었습니다.", self)
        self.completeLabel.setGeometry(70, 137, 260, 55)
        self.completeLabel.setAlignment(Qt.AlignCenter)
        self.completeLabel.setStyleSheet('font: 700 20px "Malgun Gothic"; color: #000;')


class Ui_AdminPage:
    """관리자 화면의 고정 위젯 배치 및 공지 화면 통합."""

    def setupUi(self, AdminPage):
        AdminPage.setObjectName("AdminPage")
        AdminPage.resize(1280, 800)
        AdminPage.setStyleSheet(
            "QWidget { background:white; }"
            "QWidget#sidebar { background:#e5f4fc; border-right:1px solid #444; }"
            "QPushButton#menu { background:transparent; border:0; text-align:left; padding:10px 12px; }"
            "QPushButton#menu:checked { color:#1877f2; font-weight:700; }"
            "QPushButton#action, QPushButton#page, QPushButton#noticeSendBtn { background:#48aff0; color:white; border:0; border-radius:7px; padding:8px 18px; }"
        )

        self.outer_layout = QHBoxLayout(AdminPage)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)

        # 사이드바 영역
        self.sidebar = QWidget(AdminPage)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(228)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(20, 18, 14, 20)

        self.brand_label = QLabel("Jewel", self.sidebar)
        self.brand_label.setStyleSheet("font-size:28px;font-weight:800;color:#0b3d63;")
        self.sidebar_layout.addWidget(self.brand_label)
        self.sidebar_layout.addSpacing(25)

        self.menu_buttons = []
        for title in ("차단", "차단 풀기", "공지", "회원등급"):
            button = QPushButton(title, self.sidebar)
            button.setObjectName("menu")
            button.setCheckable(True)
            self.menu_buttons.append(button)
            self.sidebar_layout.addWidget(button)
        self.sidebar_layout.addStretch()
        self.outer_layout.addWidget(self.sidebar)

        # 메인 콘텐츠 영역
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(28, 18, 28, 28)

        self.header_layout = QHBoxLayout()
        self.header_layout.addStretch()
        self.logout_button = LogoutButton()
        self.logout_button.setObjectName("logout")
        self.header_layout.addWidget(self.logout_button)
        self.content_layout.addLayout(self.header_layout)

        # 1. 기존 아이디 목록 관련 위젯들 (차단/차단풀기용)
        self.title_label = QLabel("아이디 목록", AdminPage)
        self.title_label.setStyleSheet("font-size:16px;font-weight:600;")
        self.content_layout.addWidget(self.title_label)

        self.list_box = QWidget(AdminPage)
        self.list_box.setStyleSheet("border:1px solid #222;")
        self.list_layout = QVBoxLayout(self.list_box)
        self.list_layout.setContentsMargins(16, 16, 16, 16)
        self.list_layout.setSpacing(14)

        self.member_scroll = QScrollArea(AdminPage)
        self.member_scroll.setWidgetResizable(True)
        self.member_scroll.setWidget(self.list_box)
        self.member_scroll.setMinimumHeight(500)
        self.content_layout.addWidget(self.member_scroll)

        # 페이징 및 하단 액션 버튼 (차단하기 등)
        self.page_label = QLabel("1 / 1", AdminPage)
        self.page_label.setAlignment(Qt.AlignCenter)
        self.prev_button = QPushButton("← 이전", AdminPage)
        self.next_button = QPushButton("다음 →", AdminPage)
        self.prev_button.setObjectName("page")
        self.next_button.setObjectName("page")
        
        self.pager_layout = QHBoxLayout()
        self.pager_layout.addStretch()
        self.pager_layout.addWidget(self.prev_button)
        self.pager_layout.addWidget(self.page_label)
        self.pager_layout.addWidget(self.next_button)
        self.pager_layout.addStretch()
        self.content_layout.addLayout(self.pager_layout)

        self.action_button = QPushButton("차단하기", AdminPage)
        self.action_button.setObjectName("action")
        self.content_layout.addWidget(self.action_button, alignment=Qt.AlignCenter)

        # 2. 회원등급 테이블 위젯 (회원등급 메뉴용)
        self.grade_table = QTableWidget(AdminPage)
        self.grade_table.setColumnCount(4)
        self.grade_table.setHorizontalHeaderLabels(["이름", "이메일", "현재 등급", "변경할 등급"])
        self.grade_table.setVisible(False)
        self.content_layout.insertWidget(
            self.content_layout.indexOf(self.member_scroll), self.grade_table
        )
        self.content_layout.setStretch(
            self.content_layout.indexOf(self.grade_table), 1
        )

        self.grade_save_button = QPushButton("확인", AdminPage)
        self.grade_save_button.setObjectName("action")
        self.grade_save_button.setVisible(False)
        self.content_layout.addWidget(
            self.grade_save_button, alignment=Qt.AlignCenter
        )

        # 3. [회원님 공지 UI 추가] 공지 전용 위젯들 (공지 메뉴용)
        # 회원님이 보내주신 ui 파일 좌표(x=311, y=176 등) 감각을 살려 메인 위젯 내부에 배치합니다.
        self.notice_container = QWidget(AdminPage)
        self.notice_container.setVisible(False) # 평소엔 숨김
        
        self.noticeTitleLabel = QLabel("공지(모두에게 보내기)", self.notice_container)
        self.noticeTitleLabel.setGeometry(311 - 228, 126 - 60, 220, 28) # 사이드바 너비 고려한 상대 좌표 보정
        self.noticeTitleLabel.setStyleSheet("font: 14px 'Malgun Gothic'; color: #000;")

        self.noticeTextEdit = QTextEdit(self.notice_container)
        self.noticeTextEdit.setGeometry(311 - 228, 176 - 60, 890, 503)

        self.noticeSendBtn = QPushButton("보내기", self.notice_container)
        self.noticeSendBtn.setObjectName("noticeSendBtn")
        self.noticeSendBtn.setGeometry(709 - 228, 718 - 60, 80, 36)
        self.noticeSendBtn.clicked.connect(self.handle_send_notice)

        self.content_layout.addWidget(self.notice_container)

        self.outer_layout.addLayout(self.content_layout, 1)

    def handle_send_notice(self):
        """공지 보내기 버튼 클릭 시 동작 (회원님 기존 로직 그대로 유지)"""
        content = self.noticeTextEdit.toPlainText().strip()
        if not content:
            QMessageBox.warning(None, "입력 오류", "공지 내용을 입력해주세요.")
            return

        confirm_dlg = NoticeConfirmDialog()
        if confirm_dlg.exec() != QDialog.Accepted:
            return

        complete_dlg = NoticeCompleteDialog()
        complete_dlg.exec()
        
        self.noticeTextEdit.clear()