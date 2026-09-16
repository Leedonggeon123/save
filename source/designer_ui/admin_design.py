# -*- coding: utf-8 -*-
"""관리자 화면의 고정 UI 구성 모듈."""
from PySide6.QtCore import Qt
from client.components.logout_button import LogoutButton
from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QTableWidget, QVBoxLayout, QWidget,
)


class Ui_AdminPage:
    """관리자 화면의 고정 위젯 배치."""

    def setupUi(self, AdminPage):
        AdminPage.setObjectName("AdminPage")
        AdminPage.resize(1280, 800)
        AdminPage.setStyleSheet(
            "QWidget { background:white; }"
            "QWidget#sidebar { background:#e5f4fc; border-right:1px solid #444; }"
            "QPushButton#menu { background:transparent; border:0;"
            "text-align:left; padding:10px 12px; }"
            "QPushButton#menu:checked { color:#1877f2; font-weight:700; }"
            "QPushButton#action,QPushButton#page { background:#48aff0;"
            "color:white; border:0; border-radius:7px; padding:8px 18px; }"
        )

        self.outer_layout = QHBoxLayout(AdminPage)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = QWidget(AdminPage)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(228)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(20, 18, 14, 20)

        self.brand_label = QLabel("Jewel", self.sidebar)
        self.brand_label.setStyleSheet(
            "font-size:28px;font-weight:800;color:#0b3d63;"
        )
        self.sidebar_layout.addWidget(self.brand_label)
        self.sidebar_layout.addSpacing(25)

        self.menu_buttons = []
        for title in ("차단", "차단 풀기", "공지", "회원등급"):
            button = QPushButton(title, self.sidebar)
            button.setObjectName("menu")
            button.setCheckable(True)
            self.menu_buttons.append(button)
            self.sidebar_layout.addWidget(button)
        self.sidebar_layout.addStretch()
        self.outer_layout.addWidget(self.sidebar)

        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(28, 18, 28, 28)

        self.header_layout = QHBoxLayout()
        self.header_layout.addStretch()
        self.logout_button = LogoutButton()
        self.logout_button.setObjectName("logout")
        self.header_layout.addWidget(self.logout_button)
        self.content_layout.addLayout(self.header_layout)

        self.title_label = QLabel("아이디 목록", AdminPage)
        self.title_label.setStyleSheet("font-size:16px;font-weight:600;")
        self.content_layout.addWidget(self.title_label)

        self.list_box = QWidget(AdminPage)
        self.list_box.setStyleSheet("border:1px solid #222;")
        self.list_layout = QVBoxLayout(self.list_box)
        self.list_layout.setContentsMargins(16, 16, 16, 16)
        self.list_layout.setSpacing(14)

        self.member_scroll = QScrollArea(AdminPage)
        self.member_scroll.setWidgetResizable(True)
        self.member_scroll.setWidget(self.list_box)
        self.member_scroll.setMinimumHeight(500)
        self.content_layout.addWidget(self.member_scroll)

        self.page_label = QLabel("1 / 1", AdminPage)
        self.page_label.setAlignment(Qt.AlignCenter)
        self.prev_button = QPushButton("← 이전", AdminPage)
        self.next_button = QPushButton("다음 →", AdminPage)
        self.prev_button.setObjectName("page")
        self.next_button.setObjectName("page")
        self.pager_layout = QHBoxLayout()
        self.pager_layout.addStretch()
        self.pager_layout.addWidget(self.prev_button)
        self.pager_layout.addWidget(self.page_label)
        self.pager_layout.addWidget(self.next_button)
        self.pager_layout.addStretch()
        self.content_layout.addLayout(self.pager_layout)

        self.action_button = QPushButton("차단하기", AdminPage)
        self.action_button.setObjectName("action")
        self.content_layout.addWidget(self.action_button, alignment=Qt.AlignCenter)

        self.grade_table = QTableWidget(AdminPage)
        self.grade_table.setColumnCount(4)
        self.grade_table.setHorizontalHeaderLabels(
            ["이름", "이메일", "현재 등급", "변경할 등급"]
        )
        self.grade_table.setVisible(False)
        self.content_layout.insertWidget(
            self.content_layout.indexOf(self.member_scroll), self.grade_table
        )
        self.content_layout.setStretch(
            self.content_layout.indexOf(self.grade_table), 1
        )

        self.grade_save_button = QPushButton("확인", AdminPage)
        self.grade_save_button.setObjectName("action")
        self.grade_save_button.setVisible(False)
        self.content_layout.addWidget(
            self.grade_save_button, alignment=Qt.AlignCenter
        )

        self.outer_layout.addLayout(self.content_layout, 1)


def apply_admin_table_style(table):
    """회원등급 테이블의 고정 스타일 적용."""
    from PySide6.QtWidgets import QAbstractItemView, QHeaderView

    table.horizontalHeader().setStretchLastSection(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    table.setColumnWidth(0, 220)
    table.setColumnWidth(1, 380)
    table.setColumnWidth(2, 180)
    table.setColumnWidth(3, 180)
    table.verticalHeader().setVisible(True)
    table.verticalHeader().setFixedWidth(28)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    table.setAlternatingRowColors(False)
    table.setStyleSheet(
        "QTableWidget { border:1px solid #222; gridline-color:#c6c6c6;"
        " color:#111; background:white; }"
        "QTableWidget::item { color:#111; padding:4px; }"
        "QHeaderView::section { background:#8fd0f7; color:#111;"
        " font-weight:600; border:1px solid #6ca8c7; padding:6px; }"
    )
    table.verticalHeader().setStyleSheet(
        "QHeaderView::section { background:white; color:#111;"
        " border:1px solid #c6c6c6; }"
    )
    table.horizontalHeader().setStyleSheet(
        "QHeaderView::section { background:#8fd0f7; color:#111;"
        " font-weight:600; border:1px solid #6ca8c7; padding:6px; }"
    )
