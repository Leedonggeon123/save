"""관리자 공지 기능 및 기타 클라이언트 위젯."""

from __future__ import annotations

import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from client.session import UserSession
from client.ui_common import SERVER_URL


class AdminNoticeContentWidget(QWidget):
    """관리자 공지(모두에게 보내기) 화면 위젯."""

    def __init__(self, session=None, parent=None):
        super().__init__(parent)
        self.session = session or UserSession()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 상단 타이틀 레이블
        title_label = QLabel("공지(모두에게 보내기)")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        # 텍스트 입력 영역 (QTextEdit)
        self.notice_edit = QTextEdit()
        self.notice_edit.setPlaceholderText("모든 회원에게 보낼 공지 내용을 입력하세요...")
        layout.addWidget(self.notice_edit)

        # 하단 버튼 레이아웃
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
            # 1. 서버에 존재하는 관리자 회원 조회 API를 호출합니다.
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

            # 2. 회원 목록을 돌면서 관리자 본인을 제외한 일반 회원들에게 개별 메시지를 전송합니다.
            for user in users:
                user_id = user.get("user_id")
                
                # user_id가 없거나, 로그인한 본인(관리자)이면 건너뜀
                if not user_id or user_id == admin_id:
                    continue

                # 관리자 계정은 공지 대상에서 제외
                if user.get("is_admin") == 1 or user.get("is_admin") is True:
                    continue

                # 메시지 전송 API 호출
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

            QMessageBox.information(
                self, "전송 완료", f"총 {success_count}명의 회원에게 공지를 전송했습니다."
            )
            self.notice_edit.clear()

        except requests.RequestException as e:
            QMessageBox.warning(self, "연결 오류", f"서버에 연결할 수 없습니다.\n({e})")