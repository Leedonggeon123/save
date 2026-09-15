import sys
import requests  # FastAPI 서버에 요청을 보내기 위해 사용
from client.ui_common import SERVER_URL  # 서버 주소를 공통으로 사용
from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QMessageBox
from PySide6.QtUiTools import QUiLoader
from pathlib import Path



class File_Setting_Page:
    def __init__(self, ui, user_id, file_page):                                 
        self.ui = ui
        self.user_id = user_id
        self.file_page = file_page                                                  # main에서 전달받은 file_page 객체를 저장 (다운로드 경로받기 위해 사용)
        self.file_size_limit = 0
        self.receive_path = Path("/mnt/c/Users/AIOT/Desktop")                       # 선택 안했을때 기본경로
        
        self.ui.receive_path_btn.clicked.connect(self.set_receive_path)                 # 받는 위치 설정 버튼
        self.ui.file_size_limit_btn.clicked.connect(self.set_file_size_limit)           # 파일 크기 제한 버튼
    
    
    
    def set_receive_path(self):
        folder = QFileDialog.getExistingDirectory(self.ui, "받는 위치 선택",)                   # 파일탐색기 폴더 선택
        
        if folder:                                                                      # 폴더 선택을 했다면
            print("선택한 폴더:", folder)                                               # 객체로 선택 경로 확인  
            self.receive_path = Path(folder)                                              # 선택한 경로 대입 
            self.file_page.download_path = self.receive_path                            # 파일 클래스의 다운로드 경로를 선택한 폴더로 변경


    
    def set_file_size_limit(self):
        # 사용자에게 제한 크기를 MB 단위로 입력받음
        size, ok = QInputDialog.getInt(
            self.ui,
            "파일 크기 제한",
            "제한 크기(MB)를 입력하세요:",
            0,
            0
        )

        # 사용자가 취소한 경우 함수 종료
        if not ok:
            return

        # 0은 개인 제한을 해제하고 등급 기본 제한을 사용한다는 뜻
        if size == 0:
            requested_limit = 0
            
            try:
                # 0을 FastAPI로 보내 DB에 저장
                response = requests.put(
                    f"{SERVER_URL}/files/settings/file-limit",
                    params={
                        "user_id": self.user_id,
                        "file_limit": requested_limit
                    },
                    timeout=15
                )
                            

                
            except requests.RequestException as error:
                QMessageBox.warning(
                    self.ui,
                    "연결 오류",
                    f"서버에 연결할 수 없습니다.\n{error}"
                )
                return

            # DB 저장 실패 처리
            if response.status_code != 200:
                QMessageBox.warning(
                    self.ui,
                    "저장 실패",
                    response.text
                )
                return

            # DB 저장 성공 후 현재 프로그램에 등급 기본 제한 적용
            self.file_page.max_file_size = (
                self.file_page.grade_default_limit
            )

            self.file_size_limit = 0

            print("파일 크기 제한: 등급 기본값 사용")
            return

        # 사용자가 입력한 MB를 Byte로 변환
        requested_limit = size * 1024 * 1024

        # 등급 기본 제한보다 큰 값은 설정할 수 없음
        if requested_limit > self.file_page.grade_default_limit:
            max_mb = (
                self.file_page.grade_default_limit
                / (1024 * 1024)
            )

            QMessageBox.warning(
                self.ui,
                "설정할 수 없음",
                f"현재 등급에서는 최대 {max_mb:.0f}MB까지 설정할 수 있습니다."
            )
            return

        try:
            # 입력한 제한값을 FastAPI로 보내 DB에 저장
            response = requests.put(
                f"{SERVER_URL}/files/settings/file-limit",
                params={
                    "user_id": self.user_id,
                    "file_limit": requested_limit
                },
                timeout=15
            )

        except requests.RequestException as error:
            QMessageBox.warning(
                self.ui,
                "연결 오류",
                f"서버에 연결할 수 없습니다.\n{error}"
            )
            return

        # DB 저장 실패 처리
        if response.status_code != 200:
            QMessageBox.warning(
                self.ui,
                "저장 실패",
                response.text
            )
            return

        # DB 저장에 성공한 경우 현재 프로그램에도 제한값 적용
        self.file_page.max_file_size = requested_limit
        self.file_size_limit = size

        print("파일 크기 제한 DB 저장 완료:", size, "MB")
                
            
            











# app = QApplication(sys.argv)                  # 호출을 메인py에서 

# loader = QUiLoader()

# file_ui = loader.load("source/designer_ui/file_settings.ui")

# file_setting_page = File_Setting_Page(file_ui, user_id)

# window = file_ui

                             
# window.show()

# sys.exit(app.exec())

