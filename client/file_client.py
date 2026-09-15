import requests
import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtUiTools import QUiLoader
from pathlib import Path                                                     # 파일 경로 지정하기 위해 사용


FAST_URL = "http://10.10.10.107:8000"                                       # api 서버에 연결할 아이피, 포트


class FilePage:
    def __init__(self, ui, user_id, grade, file_limit):
        self.ui = ui
                                                                                                           
        self.user_id = user_id
        self.grade = grade                                                                                   # 현재 로그인한 사용자의 등급 저장
        self.file_limit = file_limit                                                                        # 사용자에게 별도로 설정된 파일 제한값 저장
        
        
        grade_limit = {                                                                     # 등급 기본 클라우드 용량 단위는 Byte 이므로 MB에 1024 * 1024를 곱함
        "일반": 100 * 1024 * 1024,
        "실버": 200 * 1024 * 1024,
        "VIP": 500 * 1024 * 1024,
        "VVIP": 1024 * 1024 * 1024
        }

                                                                                                                
        self.grade_default_limit = grade_limit[grade]                                                            # 등급별 기본 제한값 저장

                                                                                                             
        if file_limit == 0:
            self.max_file_size = self.grade_default_limit                                                   # file_limit이 0이면 등급 기본값 사용
        else:
            self.max_file_size = file_limit


            
        self.upload_path = Path("/mnt/c/Users/AIOT/Downloads")                                                              # 업로드 파탐 열리는 경로
        self.download_path = Path("/mnt/c/Users/AIOT/Desktop")

        table = self.ui.file_table

        table.setColumnCount(3)                                                                                                   # 테이블 3열
        table.setHorizontalHeaderLabels(["선택", "파일명", "다운로드"])                                                            # 헤더 내용

        header = table.horizontalHeader()                                                                                         # 선택 열은 체크박스 크기에 맞춤
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)                                                   # 크기에 맞춰 조절                                                # 파일명 열이 남은 공간을 채움
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)                                                             # 빈공간 채우기                                                  # 다운로드 열은 버튼 크기에 맞춤
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)                                                    # 왼쪽 행 번호 숨기기
        table.verticalHeader().setVisible(False)                                                                                   # 테이블 왼쪽 숫자 숨기기

        self.ui.upload_btn.clicked.connect(self.upload_clicked)
        self.ui.refresh_btn.clicked.connect(self.load_file_list)                                                             # 새로고침시 새 테이블 보여주기
        self.ui.delete_btn.clicked.connect(self.delete_checked_files)                                                       # 삭제 클릭시


    def upload_clicked(self):                                                                                               # 파일 업로드
        file_path, _ = QFileDialog.getOpenFileName(                                                                          # 파일탐색기 열기(선택한 파일 정보는 객체에 저장)
            self.ui,
            "업로드할 파일 선택",                                                                                            # 탐색기제목
            str(self.upload_path)
        )


        if file_path:                                                                                                     # 선택을 하면
            print("선택한 파일:", file_path)

            file_size = Path(file_path).stat().st_size                                                                  # 선택한 파일 크기를 바이트 단위로 확인                 

            if file_size > self.max_file_size:                                                                              # 파일 크기가 제한 크기보다 크다면 경고창 띄우기    
                max_mb = self.max_file_size / (1024 * 1024)                                                         # byte를 mb로 변환 해서 표시 

                QMessageBox.warning(
                    self.ui,
                    "업로드 실패",
                    f"파일 크기 제한을 초과했습니다.\n"
                    f"현재 등급: {self.grade}\n"
                    f"최대 허용 크기: {max_mb:.0f}MB"
                )
                return                                                                                                      # 제한 걸리면 업로드 안하고 종료
            
            
            with open(file_path, "rb") as file:                                                                              # 제한을 통과한 경우에만 기존 업로드 실행
                response = requests.post(
                    f"{FAST_URL}/files/upload",                                                                             # 서버에 업로드 요청
                    params={"user_id": self.user_id},
                    files={"upload_file": file}
                )

            print("업로드 결과:", response.status_code)




                                                                                                                # 다운로드 함수
    def download_file(self, file_path, filename):                                                                       # file_path(서버에 있는 파일 경로) filename 저장할 때 사용할 파일 이름
        response = requests.get(
            f"{FAST_URL}/files/download",                                                                                       # 해당 인자를 통해 파일 서버의 요청 후 다운로드
            params={
                "file_path": file_path
            }
        )

        if response.status_code == 200:
            save_path, _ = QFileDialog.getSaveFileName(
                self.ui,
                "파일 저장",
                str(self.download_path / filename)
            )

            if save_path:
                with open(save_path, "wb") as file:
                    file.write(response.content)

                print("다운로드 완료:", save_path)
        else:
            print(response.text)



    def load_file_list(self):                                               # 서버 파일 목록 함수
        response = requests.get(                                        # 서버 한테 요청
            f"{FAST_URL}/files",                                        # 서버 업로드 파일 목록 조회
            params={"user_id": self.user_id}                                 # 해당 유저아이디
        )

        if response.status_code == 200:                                     # 정상 적으로 됐을떄
            data = response.json()
            file_list = data["files"]                                       # 딕셔너리 안에 정보 파일명만 가져오기

            self.show_files(file_list)                                           # 테이블 함수 호출
        else:
            print(response.text)




    def show_files(self, file_list):                                                     # 테이블 함수
        table = self.ui.file_table
        table.setRowCount(0)                                                      # 기본 테이블 모든 행 삭제

        for file_info in file_list:                                                # 서버 파일 목록
            row = table.rowCount()                                                   # 테이블 전체 열
            table.insertRow(row)                                                  # 새로운 행을 추가

            check_item = QTableWidgetItem()
            check_item.setCheckState(Qt.CheckState.Unchecked)                            # 체크박스 상태 지정

            filename = file_info["file_name"]                           # 딕셔너리에서 파일명만 추출
            file_path = file_info["file_path"]                              # 딕셔너리에서 업로드한 파일 경로 추출


            name_item = QTableWidgetItem(filename)                                          # 업로드한 파일 이름

            name_item.setData(Qt.ItemDataRole.UserRole, file_path)              # 화면에는 보이지 않지만 서버 파일 경로를 저장 (네임 아이템에 숨겨둔 경로 저장)


            download_button = QPushButton("다운로드")                       # 다운로드 버튼 생성

            download_button.clicked.connect(
                lambda checked=False,                                       # 버튼 클릭시 슬롯함수에 인자를 넣기 위해 람다 사용(함수로 만들어서 넣음) 불값은 필요없어서 false
                path=file_path,                                         # 업로드한 파일경로
                name=filename: self.download_file(path, name)                # 다운로드 함수 호출 경로와 이름 넣어서

            )

            table.setItem(row, 0, check_item)                                               # 체크박스 생성
            table.setItem(row, 1, name_item)                                                # 업로드한 파일 이름
            table.setCellWidget(row, 2, download_button)


    def delete_checked_files(self):
        table = self.ui.file_table

        for row in range(table.rowCount()):         # 테이블 전체 행 확인
            check_item = table.item(row, 0)

            if check_item.checkState() == Qt.CheckState.Checked:
                name_item = table.item(row, 1)

                file_path = name_item.data(Qt.ItemDataRole.UserRole)        # UserRole에 저장해둔 서버 파일 경로 가져오기

                response = requests.delete(                                 # 서버 한테 삭제 요청
                    f"{FAST_URL}/files",
                    params={
                        "file_path": file_path
                    }
                )

                print(
                    "삭제 결과:",
                    name_item.text(),
                    response.status_code
                )

        self.load_file_list()                # 삭제 후 테이블 새로고침
   
   
        
        
        
        
    def load_storage_usage(self):
        """
        서버에서 현재 사용 중인 전체 파일 용량을 가져옵니다.
        """

        try:
            response = requests.get(
                f"{FAST_URL}/files/usage/{self.user_id}",
                timeout=15
            )

            if response.status_code != 200:
                print("사용 용량 조회 실패:", response.text)
                return

            data = response.json()

            used_mb = data["used_mb"]

            print(f"현재 사용 용량: {used_mb}MB")

        except requests.RequestException as error:
            print("사용 용량 조회 중 서버 연결 실패:", error)     
            
            
        
        
        
         
        
# app = QApplication(sys.argv)                  # 호출을 메인py에서

# loader = QUiLoader()

# file_ui = loader.load("source/designer_ui/file_menu.ui")

# user_id = 2

# file_page = FilePage(file_ui, user_id)

# window = file_ui

# file_page.load_file_list()                                      # 파일목록 테이블 호출

# window.show()

# sys.exit(app.exec())