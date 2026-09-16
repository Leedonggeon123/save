from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFrame, QPushButton, QLabel, QVBoxLayout, QHBoxLayout

class UnblockCompleteDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 300)
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
        self.minimize_button.setFixedSize(32, 40)
        
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(32, 40)
        
        title_layout.addWidget(self.minimize_button)
        title_layout.addWidget(self.close_button)
        main_layout.addWidget(self.title_bar)
        
        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignCenter)
        
        self.complete_label = QLabel("차단이 해제 되었습니다.")
        self.complete_label.setObjectName("completeLabel")
        self.complete_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.complete_label)
        
        main_layout.addLayout(content_layout)