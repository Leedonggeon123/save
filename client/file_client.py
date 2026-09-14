import requests
import sys                                                          

from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtUiTools import QUiLoader

FAST_URL = "http://10.10.10.107:8000"                                       # api 서버에 연결할 아이피, 포트 

# 로그인 했다고 가정
user_id = 1

DOWNLOAD_FILENAME = "test.txt"                                              # 업로드한 파일 중 다운로드할 파일이름 (나중에 테이블위젯으로 클릭한 정보로 변경할예정)
DOWNLOAD_PATH = f"/mnt/c/Users/AIOT/Downloads/{DOWNLOAD_FILENAME}"          # 다운로드 경로  (임시로 다운로드경로에 설치)
SERVER_FILE_PATH = f"storage/{user_id}/{DOWNLOAD_FILENAME}"                 






def upload_clicked():                                   # 파일 업로드
    file_path,_ = QFileDialog.getOpenFileName(                                      # 파일탐색기 열기(선택한 파일 정보는 객체에 저장)
        window,
        "업로드할 파일 선택"                                                        # 탐색기제목
    )
    
    
    if file_path:                                   # 선택을 하면
        print("선택한 파일:", file_path)
        
        with open(file_path, "rb") as f:              # 선택한 파일 복사
            response = requests.post(                   
                f"{FAST_URL}/files/upload",             # 서버에 업로드 요청 
                params={"user_id": user_id},
                files={"upload_file": f}                
            )

        print("업로드 결과:", response.status_code)
        print(response.json())



def download_clicked():                                         # 파일 다운로드
    response = requests.get(
        f"{FAST_URL}/files/download",
        params={
            "file_path": SERVER_FILE_PATH                                        # 업로드된 파일 다운요청 
        }
    )

    print("다운로드 결과:", response.status_code)                               # 404면 업로드된 파일이 아닌거
    
    if response.status_code == 200:
        
        save_path,_ = QFileDialog.getSaveFileName(              # 저장할 위치 선택 
            window,
            "파일 저장",
            DOWNLOAD_FILENAME

        )
        
        if save_path:            # 파일을 선택했다면
            with open(save_path, "wb") as f:                    
                f.write(response.content)

            print("다운로드 완료", save_path)





app = QApplication(sys.argv)

loader = QUiLoader()

window = loader.load("source/designer_ui/file_menu.ui")

window.upload_btn.clicked.connect(upload_clicked)                              
window.download_btn.clicked.connect(download_clicked)


window.show()

sys.exit(app.exec())


