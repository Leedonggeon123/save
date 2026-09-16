from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from auth_db import db
except ImportError:
    try:
        from server.auth_db import db
    except ImportError:
        db = None

try:
    from .session import UserSession
except ImportError:
    try:
        from session import UserSession
    except ImportError:
        UserSession = None


class NoticeConfirmDialog(QDialog):
    """공지 전송 전 확인 다이얼로그."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # UI 규격 유지: 800 x 600
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
        self.setMaximumSize(800, 600)

        self.setWindowTitle("Jewel")

        self.setStyleSheet(
            """
            QDialog {
                background: #f7f7f7;
            }

            QPushButton#confirmButton,
            QPushButton#cancelButton {
                background: #49adf0;
                border: none;
                border-radius: 8px;
                font: 14px "Malgun Gothic";
                color: #000;
            }

            QPushButton#confirmButton:hover,
            QPushButton#cancelButton:hover {
                background: #3d9fdf;
            }
            """
        )

        self.messageLabel = QLabel(
            "공지(모두에게 보내기)\n하시겠습니까?",
            self
        )
        self.messageLabel.setGeometry(180, 244, 440, 100)
        self.messageLabel.setAlignment(Qt.AlignCenter)
        self.messageLabel.setStyleSheet(
            'font: 700 40px "Malgun Gothic"; color: #000;'
        )

        self.confirmButton = QPushButton("확인", self)
        self.confirmButton.setObjectName("confirmButton")
        self.confirmButton.setGeometry(303, 488, 80, 37)
        self.confirmButton.clicked.connect(self.accept)

        self.cancelButton = QPushButton("취소", self)
        self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.setGeometry(420, 488, 80, 37)
        self.cancelButton.clicked.connect(self.reject)


class NoticeCompleteDialog(QDialog):
    """공지 전송 완료 다이얼로그."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # UI 규격 유지: 400 x 300
        self.resize(400, 300)
        self.setMinimumSize(400, 300)
        self.setMaximumSize(400, 300)

        self.setWindowTitle("Jewel")

        self.setStyleSheet(
            """
            QDialog {
                background: #6d7582;
            }
            """
        )

        self.completeLabel = QLabel(
            "공지(모두에게 보내기)\n되었습니다.",
            self
        )
        self.completeLabel.setGeometry(70, 137, 260, 55)
        self.completeLabel.setAlignment(Qt.AlignCenter)
        self.completeLabel.setStyleSheet(
            'font: 700 20px "Malgun Gothic"; color: #000;'
        )


class AdminNoticeContentWidget(QWidget):
    """
    관리자 공지 전송 위젯.

    데이터 정의서의 USER / MESSAGES 테이블을 기준으로
    관리자 공지를 모든 비차단 사용자에게 저장한다.
    """

    MAX_CONTENT_BYTES = 1024

    def __init__(self, session=None, parent=None):
        super().__init__(parent)

        self.session = session or (
            UserSession() if UserSession else None
        )

        self.init_ui()

    def init_ui(self):
        """공지 화면 UI 구성."""

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            28,
            18,
            28,
            28
        )
        main_layout.setSpacing(14)

        # 제목
        self.notice_title_label = QLabel(
            "공지(모두에게 보내기)",
            self
        )
        self.notice_title_label.setStyleSheet(
            "font: 14px 'Malgun Gothic'; color: #000;"
        )

        main_layout.addWidget(
            self.notice_title_label
        )

        # 공지 내용 입력
        self.notice_text_edit = QTextEdit(self)

        self.notice_text_edit.setPlaceholderText(
            "모든 사용자에게 전달할 공지 내용을 입력하세요..."
        )

        self.notice_text_edit.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #111111;
                font: 14px 'Malgun Gothic';
                background: #ffffff;
            }
            """
        )

        main_layout.addWidget(
            self.notice_text_edit
        )

        main_layout.setStretch(
            main_layout.indexOf(self.notice_text_edit),
            1
        )

        # 보내기 버튼
        self.send_button = QPushButton(
            "보내기",
            self
        )

        self.send_button.setObjectName("action")
        self.send_button.setFixedSize(128, 36)

        self.send_button.clicked.connect(
            self.handle_send_notice
        )

        main_layout.addWidget(
            self.send_button,
            alignment=Qt.AlignCenter
        )

    # ---------------------------------------------------------
    # 공지 내용 검증
    # ---------------------------------------------------------

    def validate_content(self, content: str) -> bool:
        """
        공지 내용이 MESSAGES.content 제한에 맞는지 검사한다.

        데이터 정의서:
        MESSAGES.content = VARCHAR(1024)
        최대 1024 Bytes
        """

        if not content:
            QMessageBox.warning(
                self,
                "입력 오류",
                "공지 내용을 입력해주세요."
            )
            return False

        content_bytes = len(
            content.encode("utf-8")
        )

        if content_bytes > self.MAX_CONTENT_BYTES:
            QMessageBox.warning(
                self,
                "입력 오류",
                (
                    "공지 내용은 최대 "
                    f"{self.MAX_CONTENT_BYTES} Bytes까지 "
                    "입력할 수 있습니다.\n\n"
                    f"현재: {content_bytes} Bytes"
                )
            )
            return False

        return True

    # ---------------------------------------------------------
    # 관리자 권한 검사
    # ---------------------------------------------------------

    def check_admin_permission(self) -> bool:
        """
        현재 로그인 세션이 관리자 계정인지 확인한다.

        USER.is_admin 컬럼에 대응한다.
        """

        if not self.session:
            QMessageBox.warning(
                self,
                "권한 오류",
                "로그인 세션을 확인할 수 없습니다."
            )
            return False

        admin_id = getattr(
            self.session,
            "user_id",
            None
        )

        is_admin = getattr(
            self.session,
            "is_admin",
            False
        )

        if not admin_id or not is_admin:
            QMessageBox.warning(
                self,
                "권한 오류",
                "관리자 계정으로 로그인한 상태에서만 "
                "공지를 보낼 수 있습니다."
            )
            return False

        return True

    # ---------------------------------------------------------
    # 공지 전송
    # ---------------------------------------------------------

    def handle_send_notice(self):
        """공지 내용을 모든 비차단 사용자에게 저장한다."""

        # 1. 공지 내용 가져오기
        content = (
            self.notice_text_edit
            .toPlainText()
            .strip()
        )

        # 2. 공지 내용 검증
        if not self.validate_content(content):
            return

        # 3. 관리자 권한 확인
        if not self.check_admin_permission():
            return

        # 4. 관리자 ID 가져오기
        admin_id = getattr(
            self.session,
            "user_id",
            None
        )

        # 5. 전송 확인
        confirm_dlg = NoticeConfirmDialog(self)

        if confirm_dlg.exec() != QDialog.Accepted:
            return

        # 6. DB 연결 모듈 확인
        if db is None:
            QMessageBox.critical(
                self,
                "설정 오류",
                "데이터베이스 연결 모듈(auth_db)을 "
                "찾을 수 없습니다."
            )
            return

        # 전송 버튼 중복 클릭 방지
        self.send_button.setEnabled(False)

        try:
            # -------------------------------------------------
            # DB 작업
            # -------------------------------------------------
            with db() as cursor:

                # USER 테이블에서
                # 차단되지 않은 사용자만 조회
                #
                # 데이터 정의서:
                # USER.user_id
                # USER.is_banned
                cursor.execute(
                    """
                    SELECT user_id
                    FROM `USER`
                    WHERE is_banned = 0
                    """
                )

                users = cursor.fetchall()

                # MESSAGES 테이블 INSERT
                #
                # 데이터 정의서:
                # sender_id
                # receiver_id
                # content
                # is_read
                # created_at
                insert_query = """
                    INSERT INTO MESSAGES
                    (
                        sender_id,
                        receiver_id,
                        content,
                        is_read,
                        created_at
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        0,
                        NOW()
                    )
                """

                sent_count = 0

                for user in users:

                    # DB 드라이버에 따라
                    # Dict 형태 또는 Tuple 형태일 수 있음
                    if isinstance(user, dict):
                        receiver_id = user.get("user_id")
                    else:
                        receiver_id = user[0]

                    # 잘못된 데이터 방어
                    if receiver_id is None:
                        continue

                    # 관리자 본인은 공지 수신 대상에서 제외
                    if receiver_id == admin_id:
                        continue

                    cursor.execute(
                        insert_query,
                        (
                            admin_id,
                            receiver_id,
                            content
                        )
                    )

                    sent_count += 1

            # -------------------------------------------------
            # DB 작업 성공
            # -------------------------------------------------

            complete_dlg = NoticeCompleteDialog(self)
            complete_dlg.exec()

            # 전송 완료 후 입력창 초기화
            self.notice_text_edit.clear()

        except Exception as e:

            # DB 오류 발생 시 사용자에게 표시
            QMessageBox.critical(
                self,
                "전송 오류",
                (
                    "공지 저장 중 오류가 발생했습니다.\n\n"
                    f"{str(e)}"
                )
            )

        finally:
            # 오류가 발생했더라도 버튼은 다시 활성화
            self.send_button.setEnabled(True)


__all__ = [
    "AdminNoticeContentWidget",
    "NoticeConfirmDialog",
    "NoticeCompleteDialog",
]