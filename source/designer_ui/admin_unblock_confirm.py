from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFrame, QPushButton, QLabel, QVBoxLayout, QHBoxLayout

class UnblockConfirmDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setFixedSize(800, 600)
        self.setWindowTitle("Jewel")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.title_bar = QFrame()
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setFixedHeight(40)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_layout.addStretch()
        
        self.minimize_button = QPushButton("−")
        self.minimize_button.setObjectName("minimizeButton")
        self.minimize_button.setFixedSize(34, 40)
        
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(34, 40)
        
        title_layout.addWidget(self.minimize_button)
        title_layout.addWidget(self.close_button)
        main_layout.addWidget(self.title_bar)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(50, 40, 50, 40)
        
        self.message_label = QLabel("차단을 해제하시겠습니까?")
        self.message_label.setObjectName("messageLabel")
        self.message_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.message_label)
        
        content_layout.addSpacing(20)
        
        btn_layout = QHBoxLayout()
        self.confirm_button = QPushButton("확인")
        self.confirm_button.setObjectName("confirmButton")
        self.confirm_button.setFixedSize(80, 37)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setFixedSize(80, 37)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.confirm_button)
        btn_layout.addWidget(self.cancel_button)
        btn_layout.addStretch()
        
        content_layout.addLayout(btn_layout)
        main_layout.addLayout(content_layout)