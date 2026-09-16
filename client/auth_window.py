"""로그인 화면과 로그인 API 통신을 담당"""
from __future__ import annotations  # 타입 힌트 평가를 늦춰 호환성을 높입니다.

# FastAPI 서버에 HTTP 요청을 보내기 위해 사용
import requests  

from PySide6.QtCore import Qt  
from PySide6.QtGui import QFont, QPalette  
from PySide6.QtWidgets import QLabel, QMessageBox, QWidget  

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

        # Designer에서 제목 objectName이 달라져도 제목 텍스트로 찾을 수 있게 처리
        title = self.findChild(QLabel, "title_label")
        # objectName으로 찾지 못한 경우 텍스트를 기준으로 다시 찾음
        if title is None: 
            title = next(
                (label for label in self.findChildren(QLabel)
                 if label.text().strip() == "JEWEL Cloud"),
                None)

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
        # 로그인 버튼을 login() 함수로 연결
        self.ui.login_button.clicked.connect(self.login) 

    def login(self):
        """입력값을 검증하고 서버 로그인 API를 호출"""
        # 이메일 입력값의 앞뒤 공백을 제거
        email = self.ui.email_input.text().strip()  

        password = self.ui.password_input.text()  

        if not email or not password:
            # 필수값이 비어 있으면 서버 요청 없이 사용자에게 안내
            QMessageBox.warning(self, "입력 오류", "이메일과 비밀번호를 입력해주세요.")
            return

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
                is_admin = self.session.is_admin  # 서버가 반환한 관리자 여부입니다.
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
        except requests.RequestException:
            QMessageBox.critical(self, "연결 오류", "서버에 연결할 수 없습니다.")

# 다른 모듈에서 공개할 화면을 명시
__all__ = ["LoginPage"]  
