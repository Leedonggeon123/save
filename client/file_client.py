import os
import requests
import sys


from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtUiTools import QUiLoader
from pathlib import Path                                                     # 파일 경로 지정하기 위해 사용


FAST_URL = os.getenv("JEWEL_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")


class FilePage:
    def __init__(self, ui, user_id, grade, file_limit, show_dashboard):
        self.ui = ui
                                                                                                           
        self.user_id = user_id
        self.grade = grade                                                                                   # 현재 로그인한 사용자의 등급 저장
        self.file_limit = file_limit                                                                        # 사용자에게 별도로 설정된 파일 제한값 저장
        self.show_dashboard = show_dashboard                                                                    # 취소 버튼 클릭시
        self.ui.cancel_btn.clicked.connect(self.show_dashboard)
        grade_limit = {                                                                     # 등급 기본 클라우드 용량 단위는 Byte 이므로 MB에 1024 * 1024를 곱함
        "일반": 100 * 1024 * 1024,
        "비즈니스": 200 * 1024 * 1024,
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
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)                                                    # 왼쪽 행 번호 숨기기                                                                               # 테이블 왼쪽 숫자 숨기기
        table.setColumnWidth(2, 110)

        self.ui.upload_btn.clicked.connect(self.upload_clicked)
        self.ui.delete_btn.clicked.connect(self.delete_checked_files)                                                       # 삭제 클릭시
        self.ui.select_all_btn.clicked.connect(self.select_all_files)                                               # 체크박스 전체선택 기능
    
    
    
    
    
    
    def select_all_files(self):                     # 전체선택 로직
        table = self.ui.file_table

        # 하나라도 선택되지 않은 파일이 있는지 확인
        all_checked = True

        for row in range(table.rowCount()):
            check_item = table.item(row, 0)

            if check_item and check_item.checkState() != Qt.CheckState.Checked:
                all_checked = False
                break

        # 전부 선택되어 있으면 전체 해제
        if all_checked:
            for row in range(table.rowCount()):
                check_item = table.item(row, 0)

                if check_item:
                    check_item.setCheckState(Qt.CheckState.Unchecked)

        # 하나라도 선택되지 않았으면 전체 선택
        else:
            for row in range(table.rowCount()):
                check_item = table.item(row, 0)

                if check_item:
                    check_item.setCheckState(Qt.CheckState.Checked)
        
    
   
   
    def upload_clicked(self):  # 파일 업로드
        # 파일 탐색기를 열어서 업로드할 파일을 선택합니다.
        file_path, _ = QFileDialog.getOpenFileName(
            self.ui,
            "업로드할 파일 선택",
            str(self.upload_path)
        )

        # 파일을 선택했다면 업로드를 진행합니다.
        if file_path:
            print("선택한 파일:", file_path)

            # 선택한 파일의 크기를 Byte 단위로 확인합니다.
            file_size = Path(file_path).stat().st_size

            # --------------------------------------------------
            # 1. 파일 크기 제한 확인
            # --------------------------------------------------

            # 파일 크기가 설정된 최대 파일 크기보다 크면 업로드하지 않습니다.
            if file_size > self.max_file_size:
                max_mb = self.max_file_size / (1024 * 1024)

                QMessageBox.warning(
                    self.ui,
                    "업로드 실패",
                    f"파일 크기 제한을 초과했습니다.\n"
                    f"현재 등급: {self.grade}\n"
                    f"최대 허용 크기: {max_mb:.0f}MB"
                )
                return

            # --------------------------------------------------
            # 2. 클라우드 남은 용량 확인
            # --------------------------------------------------

            try:
                # 서버에 현재 사용 중인 클라우드 용량을 요청합니다.
                response = requests.get(
                    f"{FAST_URL}/files/usage/{self.user_id}",
                    timeout=15
                )

            except requests.RequestException as error:
                QMessageBox.warning(
                    self.ui,
                    "업로드 실패",
                    f"클라우드 용량을 확인할 수 없습니다.\n{error}"
                )
                return

            # 서버에서 정상적으로 용량 정보를 가져오지 못했다면 업로드하지 않습니다.
            if response.status_code != 200:
                QMessageBox.warning(
                    self.ui,
                    "업로드 실패",
                    "현재 클라우드 용량을 확인할 수 없습니다."
                )
                return

            # 서버에서 받은 용량 정보를 가져옵니다.
            data = response.json()

            # 사용 가능한 용량을 MB 단위로 가져옵니다.
            available_mb = data["available_mb"]

            # MB를 Byte 단위로 변환합니다.
            available_bytes = available_mb * 1024 * 1024

            # 파일 크기가 남은 클라우드 용량보다 크면 업로드하지 않습니다.
            if file_size > available_bytes:
                QMessageBox.warning(
                    self.ui,
                    "업로드 실패",
                    f"클라우드 저장 공간이 부족합니다.\n"
                    f"사용 가능한 용량: {available_mb:.2f}MB\n"
                    f"파일 크기: {file_size / (1024 * 1024):.2f}MB"
                )
                return

            # --------------------------------------------------
            # 3. 모든 검사를 통과했으므로 실제 업로드
            # --------------------------------------------------

            with open(file_path, "rb") as file:
                response = requests.post(
                    f"{FAST_URL}/files/upload",
                    params={
                        "user_id": self.user_id
                    },
                    files={
                        "upload_file": file
                    }
                )

            # print("업로드 결과:", response.status_code)

            # 업로드가 성공하면 파일 목록을 다시 불러옵니다.
            if response.status_code == 200:
                self.load_file_list()
            else:
                print(response.text)


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
                print("다운로드 중...")
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




 
    def show_files(self, file_list):
        table = self.ui.file_table
        table.setRowCount(0)

        for file_info in file_list:
            if file_info["type"] == "folder":               # 서버 폴더생성된걸 보이지않게 
                continue
            row = table.rowCount()
            table.insertRow(row)

            check_item = QTableWidgetItem()
            check_item.setCheckState(Qt.CheckState.Unchecked)

            filename = file_info["file_name"]
            file_path = file_info["file_path"]

            name_item = QTableWidgetItem(filename)

            name_item.setData(
                Qt.ItemDataRole.UserRole,
                file_path
            )

            download_button = QPushButton("다운로드")

            download_button.clicked.connect(
                lambda checked=False,
                    path=file_path,
                    name=filename: self.download_file(path, name)
            )

            table.setItem(row, 0, check_item)
            table.setItem(row, 1, name_item)
            table.setCellWidget(row, 2, download_button)

  
    def delete_checked_files(self):
        table = self.ui.file_table

        for row in range(table.rowCount()):
            check_item = table.item(row, 0)

            if check_item.checkState() == Qt.CheckState.Checked:
                name_item = table.item(row, 1)

                file_path = name_item.data(Qt.ItemDataRole.UserRole)

                response = requests.delete(
                    f"{FAST_URL}/files",
                    params={
                        "file_path": file_path
                    }
                )

                print("삭제 결과:", name_item.text())

        self.load_file_list()
            
        
        
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
