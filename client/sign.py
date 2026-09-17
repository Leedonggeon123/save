"""Jewel Cloud 회원가입 화면
"""
from __future__ import annotations
import sys
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton, QWidget
from requests import RequestException
from client import signup_client
from source.designer_ui.signup_design import Ui_Form

class SignupWindow(QWidget):
    """회원가입 화면의 버튼 동작과 입력 검사를 담당"""
    def __init__(self, go_login=None):
        super().__init__()
        # main_gui.py에서 stacked widget 페이지 전환용으로 사용
        self.go_login = go_login
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        title_font = QFont("Ubuntu", 102)
        title_font.setWeight(QFont.Weight.Bold)
        title_font.setBold(True)
        self.ui.title_label.setFont(title_font)
        self.ui.title_label.setStyleSheet(
            "color:#0b3d63; font-size:102px; font-weight:900;"
        )
        self.ui.title_label.setMinimumHeight(125)
        self.ui.title_label.setMaximumHeight(125)
        # 로그인 화면으로 돌아가는 버튼
        self.back_button = QPushButton("뒤로가기", self)
        # 버튼 이동
        self.back_button.setGeometry(1090, 18, 120, 38)
        self.back_button.setStyleSheet(
            "QPushButton { background:#4285f4; color:white; border:0; "
            "border-radius:6px; font-size:13px; }"
        )
        self.back_button.clicked.connect(self.back_to_login)
        self.back_button.setVisible(go_login is not None)
        # 세로 입력창 사이 간격
        self.ui.main_layout.setSpacing(14)
        self.ui.main_layout.setContentsMargins(320, 58, 320, 20)
        # 남는 높이를 위젯 사이에 자동 분배하지 않고 아래쪽에 남김
        self.ui.main_layout.setAlignment(Qt.AlignTop)
        # 제목 영역과 입력 영역을 분리
        self.ui.main_layout.insertSpacing(1, 16)
        self.ui.email_layout.setSpacing(6)
        self.ui.code_layout.setSpacing(6)
        # 버튼을 행의 아래쪽에 정렬해 입력칸보다 실제로 조금 내려 보이게 합니다.
        self.ui.email_layout.setAlignment(self.ui.check_email_button, Qt.AlignBottom)
        self.ui.code_layout.setAlignment(self.ui.send_code_button, Qt.AlignBottom)
        self.ui.code_layout.setAlignment(self.ui.verify_code_button, Qt.AlignBottom)
        # 입력 위젯이 남는 공간을 모두 차지해 행 사이가 벌어지지 않도록 높이를 고정
        for field in (
            self.ui.name_input,
            self.ui.email_input,
            self.ui.code_input,
            self.ui.password_input,
            self.ui.password_confirm_input,
        ):
            field.setFixedHeight(50)
        for button in (
            self.ui.check_email_button,
            self.ui.send_code_button,
            self.ui.verify_code_button,
        ):
            button.setFixedHeight(62)
        self.ui.timer_label.setFixedHeight(18)
        self.ui.signup_button.setFixedHeight(60)
        self.remaining_seconds = 0
        self.email_is_available = False
        self.code_is_verified = False
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_timer)
        self.ui.check_email_button.clicked.connect(self.check_email)
        self.ui.send_code_button.clicked.connect(self.send_code)
        self.ui.verify_code_button.clicked.connect(self.verify_code)
        self.ui.signup_button.clicked.connect(self.submit_signup)
        # 확인을 마친 뒤 이메일이나 인증번호가 바뀌면 기존 확인 상태를 무효화합니다.
        self.ui.email_input.textChanged.connect(self.reset_email_verification)
        self.ui.code_input.textChanged.connect(self.reset_code_verification)
        self._buttons_lowered = False

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._buttons_lowered:
            self._buttons_lowered = True
            QTimer.singleShot(0, self.lower_action_buttons)

    def lower_action_buttons(self) -> None:
        """레이아웃이 배치된 뒤 인증 관련 버튼만 2px 아래로 이동합니다."""
        for button in (
            self.ui.check_email_button,
            self.ui.send_code_button,
            self.ui.verify_code_button,
        ):
            button.move(button.x(), button.y() + 5)

    def reset_email_verification(self, _text: str = "") -> None:
        """이메일이 바뀌면 중복 확인과 인증번호 확인을 모두 다시 요구"""
        self.email_is_available = False
        self.code_is_verified = False

    def reset_code_verification(self, _text: str = "") -> None:
        """인증번호가 바뀌면 해당 인증번호의 확인 상태를 무효화"""
        self.code_is_verified = False

    def reset_form(self) -> None:
        """회원가입 화면을 다시 열 때 이전 입력값을 모두 초기화"""
        for field in (
            self.ui.name_input,
            self.ui.email_input,
            self.ui.code_input,
            self.ui.password_input,
            self.ui.password_confirm_input,
        ):
            field.clear()
        self.email_is_available = False
        self.code_is_verified = False
        self.remaining_seconds = 0
        self.timer.stop()
        self.ui.timer_label.setText("인증번호를 발송하면 유효시간이 표시됩니다.")

    def back_to_login(self) -> None:
        """뒤로가기 버튼을 눌렀을 때 로그인 화면으로 이동"""
        self.reset_form()
        if self.go_login:
            self.go_login()

    @staticmethod
    def show_error(parent: QWidget, title: str, error: Exception) -> None:
        """사용자가 읽을 수 있는 메시지를 보여줌"""
        QMessageBox.warning(parent, title, getattr(error, "user_message", str(error)))

    # 이메일(아이디) 롹인
    def check_email(self) -> None:
        email = self.ui.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "입력 오류", "구글 이메일을 입력해주세요."); return
        try:
            signup_client.check_email(email)
            self.email_is_available = True
            QMessageBox.information(self, "확인", "사용 가능한 이메일입니다.")
        except (RequestException, ValueError) as error:
            self.show_error(self, "중복 확인 실패", error)

    # 인증번호 전송
    def send_code(self) -> None:
        email = self.ui.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "입력 오류", "구글 이메일을 입력해주세요."); return
        try:
            signup_client.request_verification_code(email)
            self.code_is_verified = False
            self.remaining_seconds = 600
            self.timer.start(); self.update_timer()
            QMessageBox.information(self, "전송 완료", "인증번호를 전송했습니다. 10분 안에 입력해주세요.")
        except (RequestException, ValueError) as error:
            self.show_error(self, "전송 실패", error)

    # 메일 인증
    def verify_code(self) -> None:
        if self.remaining_seconds <= 0:
            QMessageBox.warning(self, "인증 실패", "인증번호가 만료되었습니다. 새로 요청해주세요."); return
        code = self.ui.code_input.text().strip()
        if not code:
            QMessageBox.warning(self, "인증 실패", "인증번호를 입력해주세요."); return
        if len(code) != 6 or not code.isdigit():
            QMessageBox.warning(self, "인증 실패", "인증번호는 숫자 6자리로 입력해주세요."); return
        try:
            signup_client.verify_code(self.ui.email_input.text().strip(), code)
            self.code_is_verified = True
            QMessageBox.information(self, "확인", "인증번호가 일치합니다.")
        except (RequestException, ValueError) as error:
            self.show_error(self, "인증 실패", error)

    # 회원가입
    def submit_signup(self) -> None:
        if not self.email_is_available:
            QMessageBox.warning(self, "확인 필요", "먼저 아이디 중복 확인을 해주세요."); return
        if not self.code_is_verified:
            QMessageBox.warning(self, "확인 필요", "먼저 인증번호를 확인해주세요."); return
        name = self.ui.name_input.text().strip()
        email = self.ui.email_input.text().strip()
        password = self.ui.password_input.text()
        if not name:
            QMessageBox.warning(self, "입력 오류", "이름을 입력해주세요."); return
        if password != self.ui.password_confirm_input.text():
            QMessageBox.warning(self, "입력 오류", "비밀번호가 일치하지 않습니다."); return
        if len(password) < 10 or len(password) > 20:
            QMessageBox.warning(self, "입력 오류", "비밀번호는 10자 이상 20자 이하 입력해주세요."); return
        # 비밀번호에 한글이 들어갔는지 검사
        if not all("!" <= character <= "~" for character in password):
            QMessageBox.warning(self, "입력 오류", "비밀번호에는 한글을 사용할 수 없습니다."); return
        if not any(character.isalpha() for character in password):
            QMessageBox.warning(self, "입력 오류", "비밀번호에 영문을 하나 이상 포함해주세요."); return
        if not any(character.isdigit() for character in password):
            QMessageBox.warning(self, "입력 오류", "비밀번호에 숫자를 하나 이상 포함해주세요."); return
        try:
            signup_client.signup(email, name, password, self.ui.code_input.text().strip())
            self.timer.stop(); QMessageBox.information(self, "가입 완료", "회원가입이 완료되었습니다.")
            if self.go_login:
                self.go_login()
            else:
                self.close()
        except (RequestException, ValueError) as error:
            self.show_error(self, "회원가입 실패", error)

    def update_timer(self) -> None:
        self.remaining_seconds = max(0, self.remaining_seconds - 1)
        minutes, seconds = divmod(self.remaining_seconds, 60)
        if self.remaining_seconds:
            self.ui.timer_label.setText(f"인증번호 유효시간: {minutes:02d}:{seconds:02d}")
        else:
            self.timer.stop(); self.code_is_verified = False
            self.ui.timer_label.setText("인증번호가 만료되었습니다. 새 인증번호를 요청해주세요.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SignupWindow(); window.show()
    sys.exit(app.exec())
