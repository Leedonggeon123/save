from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QPushButton, QLabel, 
    QListWidget, QVBoxLayout, QHBoxLayout
)

class UnblockMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(1280, 800)
        self.setWindowTitle("Jewel")
        
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 좌측 사이드바
        self.side_bar = QFrame()
        self.side_bar.setObjectName("sideBar")
        self.side_bar.setFixedWidth(228)
        
        sidebar_layout = QVBoxLayout(self.side_bar)
        sidebar_layout.setContentsMargins(19, 18, 0, 0)
        sidebar_layout.setSpacing(10)
        
        brand_layout = QHBoxLayout()
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(92, 72)
        self.logo_label.setScaledContents(True)
        
        self.brand_label = QLabel("Jewel")
        self.brand_label.setObjectName("brandLabel")
        brand_layout.addWidget(self.logo_label)
        brand_layout.addWidget(self.brand_label)
        sidebar_layout.addLayout(brand_layout)
        
        sidebar_layout.addSpacing(15)
        
        self.block_button = QPushButton("차단", self.side_bar)
        self.block_button.setObjectName("blockButton")
        self.block_button.setFixedHeight(48)
        
        self.unblock_button = QPushButton("차단 풀기", self.side_bar)
        self.unblock_button.setObjectName("unblockButton")
        self.unblock_button.setFixedHeight(48)
        self.unblock_button.setStyleSheet("color: #0078ff;")
        
        self.notice_button = QPushButton("공지", self.side_bar)
        self.notice_button.setObjectName("noticeButton")
        self.notice_button.setFixedHeight(48)
        
        self.membership_button = QPushButton("회원등급", self.side_bar)
        self.membership_button.setObjectName("membershipButton")
        self.membership_button.setFixedHeight(48)
        
        for btn in [self.block_button, self.unblock_button, self.notice_button, self.membership_button]:
            btn.setFixedWidth(220)
            sidebar_layout.addWidget(btn)
            
        sidebar_layout.addStretch()
        main_layout.addWidget(self.side_bar)
        
        # 우측 콘텐츠 영역
        content_layout_wrapper = QVBoxLayout()
        content_layout_wrapper.setContentsMargins(0, 0, 0, 0)
        content_layout_wrapper.setSpacing(0)
        
        self.title_bar = QFrame()
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setFixedHeight(40)
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar_layout.setSpacing(0)
        
        title_bar_layout.addStretch()
        self.minimize_button = QPushButton("−", self.title_bar)
        self.minimize_button.setObjectName("minimizeButton")
        self.minimize_button.setFixedSize(38, 40)
        
        self.close_button = QPushButton("×", self.title_bar)
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(38, 40)
        
        title_bar_layout.addWidget(self.minimize_button)
        title_bar_layout.addWidget(self.close_button)
        content_layout_wrapper.addWidget(self.title_bar)
        
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(38, 25, 38, 25)
        
        top_action_layout = QHBoxLayout()
        top_action_layout.addStretch()
        self.logout_button = QPushButton("로그아웃")
        self.logout_button.setObjectName("logoutButton")
        self.logout_button.setFixedSize(160, 44)
        top_action_layout.addWidget(self.logout_button)
        body_layout.addLayout(top_action_layout)
        
        self.title_label = QLabel("차단한 아이디 목록")
        self.title_label.setObjectName("titleLabel")
        body_layout.addWidget(self.title_label)
        
        body_layout.addSpacing(10)
        
        self.id_list_widget = QListWidget()
        body_layout.addWidget(self.id_list_widget)
        
        body_layout.addSpacing(15)
        
        bottom_action_layout = QHBoxLayout()
        bottom_action_layout.addStretch()
        self.action_button = QPushButton("차단 풀기")
        self.action_button.setObjectName("actionButton")
        self.action_button.setFixedSize(128, 36)
        bottom_action_layout.addWidget(self.action_button)
        bottom_action_layout.addStretch()
        
        body_layout.addLayout(bottom_action_layout)
        content_layout_wrapper.addWidget(body_widget)
        
        main_layout.addLayout(content_layout_wrapper)