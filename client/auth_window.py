"""로그인 화면과 로그인 API 통신을 담당"""
from __future__ import annotations  # 타입 힌트 평가를 늦춰 호환성을 높입니다.

# FastAPI 서버에 HTTP 요청을 보내기 위해 사용
import requests  

from PySide6.QtCore import QTimer, Qt  
from PySide6.QtGui import QFont, QPalette  
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QHBoxLayout, QVBoxLayout, QWidget

from source.designer_ui.login_design import Ui_LoginPage  # Designer에서 생성된 로그인 UI
from client.sign import SignupWindow  # 회원가입 화면을 재사용
from client.ui_common import SERVER_URL  # 서버 주소 환경설정
from client.session import UserSession


class LoginPage(QWidget):
    """로그인 UI를 표시하고 로그인 요청을 처리"""

    def __init__(self, show_signup, show_dashboard, show_admin=None, session=None):
        super().__init__()
        # 로그인 화면
        self.ui = Ui_LoginPage() 
        self.ui.setupUi(self)  

        # 이메일과 비밀번호 입력값은 검정색, placeholder는 회색으로 설정
        for field in (self.ui.email_input, self.ui.password_input):
            palette = field.palette() 
            palette.setColor(QPalette.ColorRole.Text, Qt.black)  
            field.setPalette(palette) 
            field.setStyleSheet( 
                "QLineEdit { background:#eeeeee; color:#000000; border:0; "
                "border-radius:7px; padding:13px 20px; font-size:22px; }"
                "QLineEdit::placeholder { color:#858585; }"
            )

        # 타이틀 텍스트
        title = self.findChild(QLabel, "title_label")
        
        if title is not None:
            # 제목이 테마에 의해 작아지지 않도록 글꼴 객체와 스타일시트를 함께 지정
            title_font = QFont("Ubuntu", 102)  
            title_font.setWeight(QFont.Weight.Bold)  
            title_font.setBold(True) 
            title.setFont(title_font)  
            title.setStyleSheet("color:#0b3d63; font-size:102px; font-weight:900;")  

        # 페이지 전환 콜백을 저장
        # 회원가입 버튼이 호출할 화면 전환 함수
        self.show_signup = show_signup        
        # 로그인 성공 후 호출할 메인 화면 전환 함수
        self.show_dashboard = show_dashboard
        self.show_admin = show_admin  
        self.session = session or UserSession()

        # Designer 버튼 클릭 시 각각의 동작 함수를 연결
        # 회원가입 버튼을 회원가입 페이지로 연결
        self.ui.signup_button.clicked.connect(self.show_signup)
        self.ui.find_password_button.clicked.connect(self.show_reset_password)
        # 로그인 버튼을 login() 함수로 연결
        self.ui.login_button.clicked.connect(self.login) 

    def show_reset_password(self):
        """이름·이메일 인증 후 비밀번호를 재설정하는 팝업을 표시합니다."""
        dialog = QDialog(self)
        dialog.setWindowTitle("비밀번호 찾기")
        dialog.setFixedSize(800, 600)
        dialog.setStyleSheet(
            "QDialog { background:white; }"
            "QLabel { color:#0b3d63; }"
            "QLineEdit { background:#eeeeee; color:#111; border:0; border-radius:7px; padding:6px 14px; font-size:16px; }"
            "QPushButton { background:#2379aa; color:white; border:0; border-radius:7px; padding:8px 14px; font-size:15px; }"
        )
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(42, 0, 42, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignVCenter)
        title = QLabel("비밀번호 찾기")
        title.setStyleSheet("font-size:26px; font-weight:800;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        content_width = 430
        guide = QLabel("이름과 이메일을 입력한 뒤\n메일로 받은 인증번호로 비밀번호를 변경하세요.")
        guide.setAlignment(Qt.AlignCenter)
        guide.setWordWrap(True)
        guide.setFixedHeight(52)
        layout.addWidget(guide, alignment=Qt.AlignHCenter)

        name_input = QLineEdit()
        name_input.setPlaceholderText("이름")
        email_input = QLineEdit()
        email_input.setPlaceholderText("이메일")
        code_input = QLineEdit()
        code_input.setPlaceholderText("이메일 인증번호 6자리")
        new_password_input = QLineEdit()
        new_password_input.setPlaceholderText("새 비밀번호 (10자 이상)")
        new_password_input.setEchoMode(QLineEdit.Password)
        confirm_input = QLineEdit()
        confirm_input.setPlaceholderText("새 비밀번호 확인")
        confirm_input.setEchoMode(QLineEdit.Password)

        # 회원가입 화면처럼 이메일·인증번호 입력칸과 버튼을 한 줄에 배치합니다.
        for field in (name_input, new_password_input, confirm_input):
            field.setFixedSize(content_width, 50)
        for field in (email_input, code_input):
            field.setFixedHeight(50)

        send_button = QPushButton("인증번호 발송")
        send_button.setFixedSize(140, 50)
        verify_button = QPushButton("인증번호 확인")
        verify_button.setFixedSize(140, 50)
        reset_button = QPushButton("비밀번호 변경")
        reset_button.setFixedSize(content_width, 50)

        layout.addWidget(name_input, alignment=Qt.AlignHCenter)
        email_container = QWidget()
        email_container.setFixedSize(content_width, 50)
        email_row = QHBoxLayout(email_container)
        email_row.setContentsMargins(0, 0, 0, 0)
        email_row.setSpacing(6)
        email_row.addWidget(email_input, 1)
        email_row.addWidget(send_button)
        layout.addWidget(email_container, alignment=Qt.AlignHCenter)
        timer_label = QLabel("인증번호를 발송하면 유효시간이 표시됩니다.")
        timer_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        timer_label.setStyleSheet("color:#858585; font-size:13px; padding:0; margin:0;")
        timer_label.setFixedSize(content_width, 12)
        layout.addWidget(timer_label, alignment=Qt.AlignHCenter)
        code_container = QWidget()
        code_container.setFixedSize(content_width, 50)
        code_row = QHBoxLayout(code_container)
        code_row.setContentsMargins(0, 0, 0, 0)
        code_row.setSpacing(6)
        code_row.addWidget(code_input, 1)
        code_row.addWidget(verify_button)
        layout.addWidget(code_container, alignment=Qt.AlignHCenter)
        layout.addWidget(new_password_input, alignment=Qt.AlignHCenter)
        layout.addWidget(confirm_input, alignment=Qt.AlignHCenter)
        layout.addWidget(reset_button, alignment=Qt.AlignHCenter)

        verified = {"value": False}
        remaining_seconds = {"value": 0}
        timer = QTimer(dialog)
        timer.setInterval(1000)

        def update_timer():
            if remaining_seconds["value"] <= 0:
                timer.stop()
                timer_label.setText("인증번호가 만료되었습니다. 다시 발송해주세요.")
                verified["value"] = False
                return
            minutes, seconds = divmod(remaining_seconds["value"], 60)
            timer_label.setText(f"인증번호 유효시간 {minutes:02d}:{seconds:02d}")
            remaining_seconds["value"] -= 1

        timer.timeout.connect(update_timer)

        def send_code():
            name = name_input.text().strip()
            email = email_input.text().strip()
            if not name or not email:
                QMessageBox.warning(dialog, "입력 오류", "이름과 이메일을 입력해주세요.")
                return
            try:
                response = requests.post(
                    f"{SERVER_URL}/api/password/reset/request-code",
                    json={"name": name, "email": email},
                    timeout=30,
                )
                if response.ok:
                    verified["value"] = False
                    remaining_seconds["value"] = 600
                    update_timer()
                    timer.start()
                    QMessageBox.information(dialog, "메일 발송", "인증번호를 이메일로 보냈습니다.")
                else:
                    QMessageBox.warning(dialog, "발송 실패", str(response.json().get("detail", "인증번호 발송에 실패했습니다.")))
            except requests.RequestException as error:
                QMessageBox.warning(dialog, "연결 오류", f"서버와 통신할 수 없습니다.\n{error}")

        def verify_code():
            email = email_input.text().strip()
            code = code_input.text().strip()
            if remaining_seconds["value"] <= 0:
                QMessageBox.warning(dialog, "인증 실패", "인증번호가 만료되었습니다. 새로 발송해주세요.")
                return
            if not email or not code:
                QMessageBox.warning(dialog, "입력 오류", "이메일과 인증번호를 입력해주세요.")
                return
            try:
                response = requests.post(
                    f"{SERVER_URL}/api/signup/verify-code",
                    json={"email": email, "verification_code": code},
                    timeout=15,
                )
                if response.ok:
                    verified["value"] = True
                    timer.stop()
                    timer_label.setText("이메일 인증 완료")
                    QMessageBox.information(dialog, "인증 완료", "이메일 인증이 완료되었습니다.")
                else:
                    QMessageBox.warning(dialog, "인증 실패", str(response.json().get("detail", "인증번호가 올바르지 않습니다.")))
            except requests.RequestException as error:
                QMessageBox.warning(dialog, "연결 오류", f"서버와 통신할 수 없습니다.\n{error}")

        def reset_password():
            name = name_input.text().strip()
            email = email_input.text().strip()
            code = code_input.text().strip()
            password = new_password_input.text()
            confirm = confirm_input.text()
            if not verified["value"]:
                QMessageBox.warning(dialog, "인증 필요", "먼저 이메일 인증을 완료해주세요.")
                return
            if not name or not email or not code or not password or not confirm:
                QMessageBox.warning(dialog, "입력 오류", "모든 항목을 입력해주세요.")
                return
            if password != confirm:
                QMessageBox.warning(dialog, "입력 오류", "새 비밀번호가 서로 일치하지 않습니다.")
                return
            try:
                response = requests.post(
                    f"{SERVER_URL}/api/password/reset",
                    json={"name": name, "email": email, "verification_code": code, "password": password},
                    timeout=15,
                )
                if response.ok:
                    QMessageBox.information(dialog, "변경 완료", "비밀번호가 변경되었습니다.")
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "변경 실패", str(response.json().get("detail", "비밀번호 변경에 실패했습니다.")))
            except requests.RequestException as error:
                QMessageBox.warning(dialog, "연결 오류", f"서버와 통신할 수 없습니다.\n{error}")

        def reset_email_state():
            verified["value"] = False
            timer.stop()
            remaining_seconds["value"] = 0
            timer_label.setText("인증번호를 발송하면 유효시간이 표시됩니다.")

        email_input.textChanged.connect(reset_email_state)
        send_button.clicked.connect(send_code)
        verify_button.clicked.connect(verify_code)
        reset_button.clicked.connect(reset_password)
        dialog.exec()

    def login(self):
        """입력값을 검증하고 서버 로그인 API를 호출"""
        # 이메일 입력값의 앞뒤 공백을 제거
        email = self.ui.email_input.text().strip()  

        password = self.ui.password_input.text()  

        if not email or not password:
            # 필수값이 비어 있으면 서버 요청 없이 사용자에게 안내
            QMessageBox.warning(self, "입력 오류", "이메일과 비밀번호를 입력해주세요.")
            return
        
        # try-except 실행 중 예외가 발생할 수 있는 코드를 안전하게 처리하기 위해
        try:
            # 클라이언트에서 FastAPI 서버의 로그인 endpoint로 POST 요청을 보냄
            # 서버 주소와 로그인 API 경로를 결합 / 서버에 입력값 JSON으로 전달 / timeout: 서버가 응답하지 않을 때 무한 대기하지 않도록 제한
            response = requests.post( f"{SERVER_URL}/api/login", json={"email": email, "password": password}, timeout=15)                     

            if response.ok:
                # HTTP 응답이면 서버 JSON에서 로그인 정보를 꺼냄
                # 서버 응답 JSON을 Python dict로 변환
                data = response.json()  
                # 인증 토큰을 저장
                self.session.update_from_login(data, email) 
                # 서버가 반환한 관리자 여부
                is_admin = self.session.is_admin 
                print("로그인 성공: 메인 화면으로 이동합니다.")  
                # JewelClient에 메인 화면 전환을 요청
                if is_admin and self.show_admin:
                    self.show_admin(self.session.access_token)
                else:
                    self.show_dashboard(self.session.access_token)  
            else:
                # 서버가 4xx/5xx를 반환하면 서버의 오류 메시지를 팝업으로 표시
                detail = response.json().get("detail", "로그인에 실패했습니다.")
                QMessageBox.warning(self, "로그인 실패", str(detail))
        # 서버에 연결하지 못한 경우
        except requests.RequestException as error:
            QMessageBox.critical(self,"연결 오류",f"서버와 통신할 수 없습니다.\n{error}")

# 다른 모듈에서 공개할 화면을 명시
__all__ = ["LoginPage"]  
