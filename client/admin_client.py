# 관리자 클라이언트 메인 및 공지 기능 위젯.

from __future__ import annotations

import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from client.components.brand_header import BrandHeader
from client.session import UserSession
from client.ui_common import SERVER_URL


class AdminNoticeContentWidget(QWidget):
    """관리자 공지(모두에게 보내기) 화면 위젯 (오른쪽 메인 콘텐츠 영역)."""

    def __init__(self, session=None, parent=None):
        super().__init__(parent)
        self.session = session or UserSession()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # 1. 화면 타이틀 레이블 (우측 메인 영역 상단 중앙 또는 깔끔한 정렬)
        title_label = QLabel("공지(모두에게 보내기)")
        title_label.setStyleSheet(
            "color: #0b3d63; font-family: 'Ubuntu'; font-size: 20px; font-weight: bold;"
        )
        layout.addWidget(title_label)

        # 2. 텍스트 입력 영역 (QTextEdit)
        self.notice_edit = QTextEdit()
        self.notice_edit.setPlaceholderText("모든 회원에게 보낼 공지 내용을 입력하세요...")
        layout.addWidget(self.notice_edit)

        # 3. 하단 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.send_button = QPushButton("보내기")
        self.send_button.setFixedSize(100, 35)
        self.send_button.clicked.connect(self.send_notice)
        button_layout.addWidget(self.send_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def send_notice(self):
        message = self.notice_edit.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "입력 오류", "공지 내용을 입력해주세요.")
            return

        if QMessageBox.question(
            self, "공지 전송", "모든 회원에게 공지를 전송하시겠습니까?"
        ) != QMessageBox.StandardButton.Yes:
            return

        admin_id = getattr(self.session, "user_id", None)
        if not admin_id:
            QMessageBox.warning(self, "권한 오류", "관리자 세션 정보가 없습니다.")
            return

        try:
            response = requests.get(
                f"{SERVER_URL}/api/admin/grades",
                params={"admin_user_id": admin_id},
                timeout=10,
            )
            
            if not response.ok:
                QMessageBox.warning(self, "전송 실패", "회원 목록을 불러오지 못했습니다.")
                return

            data = response.json()
            users = data.get("users", [])
            
            if not users:
                QMessageBox.warning(self, "전송 실패", "등록된 회원이 없습니다.")
                return

            notice_content = f"[공지] {message}"
            success_count = 0

            for user in users:
                user_id = user.get("user_id")
                if not user_id or user_id == admin_id:
                    continue

                if user.get("is_admin") == 1 or user.get("is_admin") is True:
                    continue

                try:
                    msg_response = requests.post(
                        f"{SERVER_URL}/api/messages",
                        json={
                            "sender_id": admin_id,
                            "receiver_id": user_id,
                            "content": notice_content,
                        },
                        timeout=5,
                    )
                    if msg_response.ok:
                        success_count += 1
                except requests.RequestException:
                    continue

            QMessageBox.information(
                self, "전송 완료", f"총 {success_count}명에게 공지를 전송했습니다."
            )
            self.notice_edit.clear()

        except requests.RequestException as e:
            QMessageBox.warning(self, "연결 오류", f"서버에 연결할 수 없습니다.\n({e})")


class AdminMainWindow(QWidget):
    """관리자 메인 창 (왼쪽 파란색 사이드바에 BrandHeader 배치)."""

    def __init__(self, session=None, parent=None):
        super().__init__(parent)
        self.session = session or UserSession()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. 왼쪽 파란색 사이드바 영역 ---
        sidebar_widget = QWidget()
        sidebar_widget.setStyleSheet("background-color: #e3f2fd;")  # 연한 파란색 배경
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(15)

        # [핵심] 파란색 칸 상단에 BrandHeader 배치 (다이아몬드 아이콘 + Jewel 글씨)
        brand_header = BrandHeader(title="Jewel", parent=self)
        sidebar_layout.addWidget(brand_header)

        sidebar_layout.addSpacing(20)

        # 사이드바 메뉴 버튼들 (예시)
        self.btn_notice = QPushButton("공지")
        self.btn_notice.setStyleSheet("text-align: left; border: none; font-size: 14px; color: #007acc;")
        sidebar_layout.addWidget(self.btn_notice)

        sidebar_layout.addStretch()

        # 사이드바 고정 너비 설정
        sidebar_widget.setFixedSize(220, 700)
        main_layout.addWidget(sidebar_widget)

        # --- 2. 오른쪽 메인 콘텐츠 영역 ---
        self.content_stack = QStackedWidget()
        
        # 공지 위젯 추가
        self.notice_widget = AdminNoticeContentWidget(session=self.session)
        self.content_stack.addWidget(self.notice_widget)

        main_layout.addWidget(self.content_stack)
        self.setLayout(main_layout)


__all__ = ["AdminNoticeContentWidget", "AdminMainWindow"]