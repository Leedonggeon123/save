"""로그인 화면과 로그인 API 통신을 담당"""
from __future__ import annotations  # 타입 힌트 평가를 늦춰 호환성을 높입니다.

# FastAPI 서버에 HTTP 요청을 보내기 위해 사용
import requests  

from PySide6.QtCore import Qt  
from PySide6.QtGui import QFont, QPalette  
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

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
        self.ui.find_id_button.clicked.connect(self.show_find_id)
        # 로그인 버튼을 login() 함수로 연결
        self.ui.login_button.clicked.connect(self.login) 

    def show_find_id(self):
        """이름과 전화번호로 가입 이메일을 찾는 팝업을 표시합니다."""
        dialog = QDialog(self)
        dialog.setWindowTitle("아이디 찾기")
        dialog.setFixedSize(800, 600)
        dialog.setStyleSheet(
            "QDialog { background:white; }"
            "QLabel { color:#0b3d63; }"
            "QLineEdit { background:#eeeeee; color:#111; border:0; border-radius:7px; padding:6px 14px; font-size:16px; }"
            "QPushButton { background:#2379aa; color:white; border:0; border-radius:7px; padding:12px; font-size:16px; }"
        )
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(42, 32, 42, 32)
        layout.setSpacing(14)
        title = QLabel("아이디 찾기")
        title.setStyleSheet("font-size:26px; font-weight:800;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        guide = QLabel("가입할 때 입력한 이름과 전화번호를 입력해주세요.")
        guide.setAlignment(Qt.AlignCenter)
        layout.addWidget(guide)
        name_input = QLineEdit()
        name_input.setPlaceholderText("이름")
        phone_input = QLineEdit()
        phone_input.setPlaceholderText("전화번호 (010-1234-5678)")
        name_input.setFixedHeight(33)
        phone_input.setFixedHeight(33)
        layout.addWidget(name_input)
        layout.addWidget(phone_input)
        find_button = QPushButton("아이디 찾기")
        layout.addWidget(find_button)

        def find_id():
            name = name_input.text().strip()
            phone = phone_input.text().strip()
            if not name or not phone:
                QMessageBox.warning(dialog, "입력 오류", "이름과 전화번호를 입력해주세요.")
                return
            if len(phone) != 13 or phone[:3] != "010" or phone[3] != "-" or phone[8] != "-" or not phone.replace("-", "").isdigit():
                QMessageBox.warning(dialog, "입력 오류", "전화번호는 010-1234-5678 형식으로 입력해주세요.")
                return
            try:
                response = requests.post(
                    f"{SERVER_URL}/api/find-id", json={"name": name, "phone": phone}, timeout=10
                )
                if response.ok:
                    QMessageBox.information(dialog, "아이디 확인", f"가입 아이디: {response.json()['email']}")
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "조회 실패", str(response.json().get("detail", "일치하는 회원 정보가 없습니다.")))
            except requests.RequestException:
                QMessageBox.warning(dialog, "연결 오류", "서버에 연결할 수 없습니다.")

        find_button.clicked.connect(find_id)
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
