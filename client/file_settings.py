import sys

from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QMessageBox
from PySide6.QtUiTools import QUiLoader
from pathlib import Path

user_id = 1


class File_Setting_Page:
    def __init__(self, ui, user_id, file_page):                                 
        self.ui = ui
        self.user_id = user_id
        self.file_page = file_page                                                  # main에서 전달받은 file_page 객체를 저장 (다운로드 경로받기 위해 사용)
        self.receive_path = Path("/mnt/c/Users/AIOT/Desktop")                       # 선택 안했을때 기본경로
        
        self.ui.receive_path_btn.clicked.connect(self.set_receive_path)                 # 받는 위치 설정 버튼
        self.ui.file_size_limit_btn.clicked.connect(self.set_file_size_limit)           # 파일 크기 제한 버튼
    
    
    
    def set_receive_path(self):
        folder = QFileDialog.getExistingDirectory(self.ui, "받는 위치 선택",)                   # 파일탐색기 폴더 선택
        
        if folder:                                                                      # 폴더 선택을 했다면
            print("선택한 폴더:", folder)                                               # 객체로 선택 경로 확인  
            self.receive_path = Path(folder)                                              # 선택한 경로 대입 
            self.file_page.download_path = self.receive_path                            # 파일 클래스의 다운로드 경로를 선택한 폴더로 변경


    
    def set_file_size_limit(self):                                                          # 파일 크기 제한 함수
        size, ok = QInputDialog.getInt(
            self.ui,
            "파일 크기 제한",
            "제한 크기(MB)를 입력하세요:",
            0,
            0
        )

        if ok:                                                                                               
            if size == 0:                                                                            # 0이면 등급 기본 제한으로 되돌림
                self.file_page.max_file_size = (self.file_page.grade_default_limit)
                self.file_size_limit = 0
                print("파일 크기 제한: 등급 기본값 사용")
                return
                                                                                           
            requested_limit = size * 1024 * 1024                                                    # 사용자가 입력한 MB를 Byte로 변환
                 
                                                                                        
            if requested_limit > self.file_page.grade_default_limit:                                    # 등급 기본 제한보다 크게 설정하는지 확인
                
                max_mb = (self.file_page.grade_default_limit / (1024 * 1024))

                QMessageBox.warning(
                    self.ui,
                    "설정할 수 없음",
                    f"현재 등급에서는 최대 {max_mb:.0f}MB까지 설정할 수 있습니다."
                )
                return
                      
                                                                                  
            self.file_page.max_file_size = requested_limit                                                       # 등급 제한 이하인 경우에만 적용
            self.file_size_limit = size
            print("파일 크기 제한:", size, "MB")
            
            
            
# app = QApplication(sys.argv)                  # 호출을 메인py에서 

# loader = QUiLoader()

# file_ui = loader.load("source/designer_ui/file_settings.ui")

# file_setting_page = File_Setting_Page(file_ui, user_id)

# window = file_ui

                             
# window.show()

# sys.exit(app.exec())

