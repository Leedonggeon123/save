"""관리자 전체 공지"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QLabel, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QWidget
)

# 세션 파일 경로에 맞춰 임포트 (필요 시 수정)
try:
    from .session import UserSession
except ImportError:
    UserSession = None


class NoticeConfirmDialog(QDialog):
    """공지 전송 전 확인 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Jewel")
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
        self.setMaximumSize(800, 600)
        
        # 팀원의 확인/취소 버튼 및 배경 스타일 적용
        self.setStyleSheet(
            'QDialog { background: #f7f7f7; } '
            'QPushButton#confirmButton, QPushButton#cancelButton { '
            'background: #49adf0; border: none; border-radius: 8px; font: 14px "Malgun Gothic"; color: #000; '
            '}'
        )

        # 메시지 레이블 (팀원의 디자인 위치/폰트 감각 반영)
        self.message_label = QLabel("공지(모두에게 보내기)\n하시겠습니까?", self)
        self.message_label.setGeometry(180, 244, 440, 100)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet('font: 700 40px "Malgun Gothic"; color: #000;')

        # 확인 버튼
        self.confirm_button = QPushButton("확인", self)
        self.confirm_button.setObjectName("confirmButton")
        self.confirm_button.setGeometry(303, 488, 80, 37)
        self.confirm_button.clicked.connect(self.accept)

        # 취소 버튼
        self.cancel_button = QPushButton("취소", self)
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setGeometry(420, 488, 80, 37)
        self.cancel_button.clicked.connect(self.reject)


class NoticeCompleteDialog(QDialog):
    """공지 전송 완료 다이얼로그 (팀원 완료 창 스타일 반영)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Jewel")
        self.resize(400, 300)
        self.setMinimumSize(400, 300)
        self.setMaximumSize(400, 300)
        self.setStyleSheet("QDialog { background: #6d7582; }")

        self.complete_label = QLabel("공지(모두에게 보내기)\n되었습니다.", self)
        self.complete_label.setGeometry(70, 137, 260, 55)
        self.complete_label.setAlignment(Qt.AlignCenter)
        self.complete_label.setStyleSheet('font: 700 20px "Malgun Gothic"; color: #000;')


class AdminNoticeContentWidget(QWidget):
    """팀원 메인 관리자 페이지의 콘텐츠 영역에 들어갈 공지 위젯."""

    def __init__(self, session=None, parent=None):
        super().__init__(parent)
        self.session = session or (UserSession() if UserSession else None)
        self.init_ui()

    def init_ui(self):
        # 팀원의 우측 메인 콘텐츠 영역 여백 및 레이아웃 규격에 맞춤
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 18, 28, 28)
        main_layout.setSpacing(14)

        # 공지 제목 레이블 (팀원의 타이틀 규격과 일치)
        self.notice_title_label = QLabel("공지(모두에게 보내기)", self)
        self.notice_title_label.setStyleSheet("font: 14px 'Malgun Gothic'; color: #000;")
        main_layout.addWidget(self.notice_title_label)

        # 내용 입력창 (QTextEdit) - 팀원이 구성한 리스트/스크롤 영역 크기와 조화되도록 설정
        self.notice_text_edit = QTextEdit(self)
        self.notice_text_edit.setPlaceholderText("모든 사용자에게 전달할 공지 내용을 입력하세요...")
        self.notice_text_edit.setStyleSheet(
            "QTextEdit { border: 1px solid #111111; font: 14px 'Malgun Gothic'; background: #ffffff; }"
        )
        main_layout.addWidget(self.notice_text_edit)
        main_layout.setStretch(main_layout.indexOf(self.notice_text_edit), 1)

        # 하단 보내기 버튼 (팀원의 action 버튼 스타일과 연동)
        self.send_button = QPushButton("보내기", self)
        self.send_button.setObjectName("action")  # 팀원의 action 버튼 스타일시트가 적용되도록 ID 지정
        self.send_button.setFixedSize(128, 36)
        self.send_button.clicked.connect(self.handle_send_notice)
        
        main_layout.addWidget(self.send_button, alignment=Qt.AlignCenter)

    def handle_send_notice(self):
        content = self.notice_text_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "입력 오류", "공지 내용을 입력해주세요.")
            return

        # 확인 다이얼로그 호출
        confirm_dlg = NoticeConfirmDialog(self)
        if confirm_dlg.exec() != QDialog.Accepted:
            return

        # 완료 창 띄우기
        complete_dlg = NoticeCompleteDialog(self)
        complete_dlg.exec()
        
        self.notice_text_edit.clear()


__all__ = ["AdminNoticeContentWidget", "NoticeConfirmDialog", "NoticeCompleteDialog"]