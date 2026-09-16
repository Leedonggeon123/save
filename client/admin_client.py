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

        try:
            response = requests.post(
                f"{SERVER_URL}/api/admin/notice",
                json={
                    "admin_user_id": self.session.user_id,
                    "message": message,
                },
                timeout=10,
            )
            if not response.ok:
                QMessageBox.warning(
                    self, "전송 실패",
                    str(response.json().get("detail", "공지 전송에 실패했습니다.")),
                )
                return

            QMessageBox.information(self, "전송 완료", "공지가 성공적으로 전송되었습니다.")
            self.notice_edit.clear()
        except requests.RequestException:
            QMessageBox.warning(self, "연결 오류", "서버에 연결할 수 없습니다.")


__all__ = ["AdminNoticeContentWidget"]