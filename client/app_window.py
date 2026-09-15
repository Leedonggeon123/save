"""분리된 클라이언트 화면을 조립하고 전환하는 모듈"""
from __future__ import annotations  

import sys  
from PySide6.QtWidgets import QApplication, QStackedWidget  # 여러 페이지를 겹쳐 관리합

from client.auth_window import LoginPage      # 로그인 페이지
from client.sign import SignupWindow          # 회원가입 페이지
from client.main_window import DashboardPage  # 로그인 후 메인 페이지
from client.settings_window import PersonalSettingsPage, SettingsPage
from client.admin_window import AdminPage  # 설정 페이지들
from client.session import UserSession


class JewelClient(QStackedWidget):
    """로그인·회원가입·메인·설정 페이지를 하나의 창에서 전환"""

    def __init__(self):
        super().__init__()
        # 운영체제 창 제목 설정
        self.setWindowTitle("JEWEL Cloud") 
        self.resize(1280, 800)  
        
         # 페이지 바깥 배경을 흰색으로 고정
        self.setStyleSheet("QStackedWidget { background-color: white; }")
        self.session = UserSession() 
        # 각 페이지를 생성하고, 화면 전환용 콜백을 전달
        # 로그인 페이지
        self.login_page = LoginPage(self.show_signup, self.show_dashboard, self.show_admin, self.session)  
        # 회원가입 완료 후 로그인화면 돌아오도록
        self.signup_page = SignupWindow(go_login=self.show_login)  
        # 로그인 후 메인 페이지
        self.dashboard_page = DashboardPage(self.show_login, self.show_settings)  
        # 설정 메뉴 페이지
        self.settings_page = SettingsPage(self.show_dashboard, self.show_login, self.show_personal) 
        # 개인설정 상세 페이지
        self.personal_page = PersonalSettingsPage(self.show_settings, self.show_login, self.session)
        self.admin_page = AdminPage(self.show_login)

        # 생성한 페이지를 QStackedWidget에 등록
        self.addWidget(self.login_page)      # index 0: 로그인
        self.addWidget(self.signup_page)     # index 1: 회원가입
        self.addWidget(self.dashboard_page)  # index 2: 메인
        self.addWidget(self.settings_page)   # index 3: 설정 메뉴
        self.addWidget(self.personal_page)
        self.addWidget(self.admin_page)      # index 5: 관리자
        
        # 앱 시작 시 로그인 페이지 표시
        self.setCurrentWidget(self.login_page) 

    def show_signup(self):
        """로그인 화면에서 회원가입 화면으로 이동"""
        # 이전에 입력한 회원가입 데이터를 초기화
        self.signup_page.reset_form()  
        # 현재 화면을 회원가입 페이지로 변경
        self.setCurrentWidget(self.signup_page)  

    def show_login(self):
        """로그아웃 또는 회원가입 완료 후 로그인 화면으로"""
        # 이전에 입력했던들 내용 초기화
        self.login_page.ui.email_input.clear() 
        self.login_page.ui.password_input.clear()  
        self.personal_page.reset_all_form() 
        # 개인설정 페이지 초기화
        self.personal_page.select_category(0)
        self.session.clear()  
        # 로그인 페이지
        self.setCurrentWidget(self.login_page)  

    def show_admin(self, access_token=None):
        """관리자 계정 로그인 성공 시 관리자 화면으로 이동합니다."""
        self.admin_page.access_token = access_token
        self.setCurrentWidget(self.admin_page)

    def show_dashboard(self, access_token=None):
        """로그인이 성공했을 때 메인 화면으로 이동"""
        # 메인 페이지에 인증 토큰 전달
        self.dashboard_page.access_token = access_token 
        # 현재 화면을 메인 페이지로 변경
        self.setCurrentWidget(self.dashboard_page) 

    def show_settings(self):
        """메인 화면에서 설정 메뉴로 이동"""
        # 설정 메뉴 페이지를 표시
        self.setCurrentWidget(self.settings_page) 

    def show_personal(self):
        """설정 메뉴에서 개인설정 페이지로 이동"""
        # 로그인한 사용자 ID를 개인설정 페이지에 전달
        # 비밀번호 입력칸 초기화
        self.personal_page.reset_form() 
        # 개인설정에 들어올 때 서비스 화면부터 표시
        self.personal_page.select_category(0)
        # 로그인한 사람의 이름과 이메일을 개인정보 화면에 표시
        self.personal_page.set_user_info(self.session.name, self.session.email)  
        # USER_SETTINGS의 기본 이메일을 서버에서 조회
        self.personal_page.load_default_email()  
        # 개인설정 페이지 전환
        self.setCurrentWidget(self.personal_page) 


# 이 파일을 직접 실행했을 때도 동일한 JewelClient를 실행
if __name__ == "__main__":
    app = QApplication(sys.argv) 
    window = JewelClient()
    window.show()  
    sys.exit(app.exec()) 
