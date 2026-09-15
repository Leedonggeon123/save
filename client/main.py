import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader
from client.session import UserSession

from client.file_client import FilePage                            # 파일 부분 호출 
from client.file_settings import File_Setting_Page                 # 파일 설정 부분 호출











# user_id = 2
# grade = "일반"
# file_limit = 0

                                                                            # 로그인 성공시     # 해당 정보 넘겨받음
user_session = UserSession()


















# ==============
#   파일 부분
# ==============

# 파일 창 호출

app = QApplication(sys.argv)

loader = QUiLoader()

file_ui = loader.load("source/designer_ui/file_menu.ui")

file_page = FilePage(file_ui, user_session.user_id, user_session.grade, user_session.file_limit)          # 파일 기능 클래스 생성

# ================
# 파일 설정 부분
# ================

file_setting_ui = loader.load("source/designer_ui/file_settings.ui")
file_setting_page = File_Setting_Page(file_setting_ui, user_session.user_id, file_page)          # 파일 클래스 객체를 인자에 전달



file_page.load_file_list()                                      # 파일목록 테이블 호출

file_ui.show()                                               # 파일 부분 보여주기
file_setting_ui.show()                                      # 파일 설정 호출


sys.exit(app.exec())


