"""Existing PySide6 login screen connected to the MariaDB-backed FastAPI API."""
import os, sys, requests
from PySide6.QtWidgets import QApplication, QMessageBox
from login_design import LoginWidget

SERVER_URL = os.getenv("JEWEL_SERVER_URL", "http://127.0.0.1:8000")

class ClientApp(LoginWidget):
    def __init__(self):
        super().__init__()
        self.login_btn.clicked.connect(self.attempt_login)

    def attempt_login(self):
        email = self.email_input.text().strip(); password = self.password_input.text()
        if not email or not password: return
        try:
            response = requests.post(f"{SERVER_URL}/api/login", json={"email": email, "password": password}, timeout=10)
            if response.status_code == 200:
                self.access_token = response.json()["token"]
                QMessageBox.information(self, "로그인 성공", "로그인되었습니다.")
            else:
                detail = response.json().get("detail", "아이디 또는 비밀번호를 확인해주세요.")
                QMessageBox.warning(self, "로그인 실패", detail)
        except requests.RequestException:
            QMessageBox.critical(self, "연결 오류", "서버와 통신할 수 없습니다.")

if __name__ == "__main__":
    app = QApplication(sys.argv); client = ClientApp(); client.show(); sys.exit(app.exec())
