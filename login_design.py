# design.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton)
from PySide6.QtCore import Qt

class LoginWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JEWEL Cloud - Login")
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # 타이틀
        title_label = QLabel("JEWEL Cloud")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title_label)

        # 입력 폼
        form_layout = QVBoxLayout()
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("구글 이메일 (아이디)") # 요구사항을 반영한 힌트 텍스트[cite: 1]
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("비밀번호")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        layout.addLayout(form_layout)

        # 버튼 영역
        button_layout = QHBoxLayout()
        self.login_btn = QPushButton("로그인")
        self.find_id_btn = QPushButton("아이디찾기")
        self.signup_btn = QPushButton("회원가입")

        # 시각적 피로도를 낮춘 깔끔한 톤 스타일링
        self.login_btn.setStyleSheet("background-color: #2b78e4; color: white; padding: 5px;")
        
        button_layout.addWidget(self.find_id_btn)
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.signup_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        
       