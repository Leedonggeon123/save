"""관리자 화면 기능과 서버 API 연결."""
from __future__ import annotations

import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QMessageBox,
    QTableWidgetItem, QWidget,
)

from source.designer_ui.admin_design import Ui_AdminPage, apply_admin_table_style
from client.components.logout_button import LogoutButton
from client.session import UserSession
from client.ui_common import SERVER_URL


class AdminPage(QWidget):
    """관리자 메뉴와 회원 관리 기능 연결."""

    PAGE_SIZE = 10

    def __init__(self, logout, session=None):
        super().__init__()
        self.ui = Ui_AdminPage()
        self.ui.setupUi(self)
        self.logout = logout
        self.session = session or UserSession()
        self.mode = "ban"
        self.current_page = 1
        self.total_pages = 1
        self.member_checks = []
        self.grade_rows = []

        # Designer UI 위젯을 기능 코드에서 사용
        self.menu_buttons = self.ui.menu_buttons
        self.title_label = self.ui.title_label
        self.list_box = self.ui.list_box
        self.list_layout = self.ui.list_layout
        self.member_scroll = self.ui.member_scroll
        self.page_label = self.ui.page_label
        self.prev_button = self.ui.prev_button
        self.next_button = self.ui.next_button
        self.action_button = self.ui.action_button
        self.grade_table = self.ui.grade_table
        self.grade_save_button = self.ui.grade_save_button

        self.ui.logout_button.clicked.connect(self.logout)
        for button in self.menu_buttons:
            button.clicked.connect(
                lambda checked, name=button.text(): self.select_menu(name)
            )
        self.prev_button.clicked.connect(self.previous_page)
        self.next_button.clicked.connect(self.next_page)
        self.action_button.clicked.connect(self.block_selected)
        self.grade_save_button.clicked.connect(self.save_grades)

        # 관리자 로그인 전에는 회원 목록 API를 호출하지 않습니다.
        # 로그인 완료 후 app_window.show_admin()에서 최초 조회합니다.
        self.select_menu("차단")

    # 왼쪽 메뉴에 따라 회원 목록과 등급 화면 전환
    def select_menu(self, name):
        for button in self.menu_buttons:
            button.setChecked(button.text() == name)
        if name == "회원등급":
            self.list_box.setVisible(False)
            self.member_scroll.setVisible(False)
            self.prev_button.setVisible(False)
            self.next_button.setVisible(False)
            self.page_label.setVisible(False)
            self.action_button.setVisible(False)
            self.grade_table.setVisible(True)
            self.grade_save_button.setVisible(True)
            self.title_label.setText("회원등급")
            self.load_grades()
            return

        self.list_box.setVisible(True)
        self.member_scroll.setVisible(True)
        self.prev_button.setVisible(True)
        self.next_button.setVisible(True)
        self.page_label.setVisible(True)
        self.action_button.setVisible(True)
        self.grade_table.setVisible(False)
        self.grade_save_button.setVisible(False)
        if name not in ("차단", "차단 풀기"):
            return
        self.mode = "unban" if name == "차단 풀기" else "ban"
        self.current_page = 1
        self.title_label.setText(
            "차단한 아이디 목록" if self.mode == "unban" else "아이디 목록"
        )
        self.action_button.setText(
            "차단 풀기" if self.mode == "unban" else "차단하기"
        )
        self.load_members()

    # 페이지 전환 전 기존 체크박스 제거
    def clear_rows(self):
        self.member_checks.clear()
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # 차단 상태에 맞는 회원 목록 API 조회
    def load_members(self):
        if not self.session.user_id:
            self.render_members([], 1)
            return
        try:
            response = requests.get(
                f"{SERVER_URL}/api/admin/users",
                params={
                    "admin_user_id": self.session.user_id,
                    "page": self.current_page,
                    "page_size": self.PAGE_SIZE,
                    "banned": self.mode == "unban",
                },
                timeout=10,
            )
            if not response.ok:
                QMessageBox.warning(
                    self, "조회 실패",
                    str(response.json().get("detail", "회원 목록을 불러올 수 없습니다.")),
                )
                return
            data = response.json()
            self.total_pages = max(1, int(data.get("total_pages", 1)))
            self.render_members(data.get("users", []), self.current_page)
        except requests.RequestException as error:
            # 실제 요청 주소와 오류를 함께 표시해 원인(IP/포트/경로)을 확인합니다.
            QMessageBox.warning(
                self,
                "연결 오류",
                f"서버에 연결할 수 없습니다.\n{SERVER_URL}/api/admin/users\n{error}",
            )

    # 현재 페이지 회원을 체크박스로 구성
    def render_members(self, members, page):
        self.clear_rows()
        for member in members:
            user_id = int(member["user_id"])
            label = f"{member.get('email', '')} ({member.get('name', '')})"
            if member.get("is_banned"):
                label += " [차단됨]"
            checkbox = QCheckBox(label)
            checkbox.setStyleSheet("border:0;")
            self.list_layout.addWidget(checkbox)
            self.member_checks.append((user_id, checkbox))
        self.list_layout.addStretch()
        self.current_page = page
        self.page_label.setText(f"{page} / {self.total_pages}")
        self.prev_button.setEnabled(page > 1)
        self.next_button.setEnabled(page < self.total_pages)

    # 이전 회원 목록 페이지로 이동
    def previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_members()

    # 다음 회원 목록 페이지로 이동
    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_members()

    # 선택 회원의 차단 또는 차단 해제 요청
    def block_selected(self):
        selected = [
            user_id for user_id, checkbox in self.member_checks
            if checkbox.isChecked()
        ]
        if not selected:
            QMessageBox.warning(self, "선택 필요", "차단할 아이디를 선택해주세요.")
            return
        action_name = "차단 해제" if self.mode == "unban" else "차단"
        if QMessageBox.question(
            self, f"{action_name} 확인",
            f"선택한 아이디를 {action_name}하시겠습니까?",
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            endpoint = "unban" if self.mode == "unban" else "ban"
            response = requests.post(
                f"{SERVER_URL}/api/admin/users/{endpoint}",
                json={"admin_user_id": self.session.user_id, "user_ids": selected},
                timeout=10,
            )
            if not response.ok:
                QMessageBox.warning(
                    self, f"{action_name} 실패",
                    str(response.json().get("detail", f"{action_name}에 실패했습니다.")),
                )
                return
            QMessageBox.information(
                self, f"{action_name} 완료",
                f"선택한 아이디를 {action_name}했습니다.",
            )
            self.load_members()
        except requests.RequestException:
            QMessageBox.warning(self, "연결 오류", "서버에 연결할 수 없습니다.")

    # 회원별 현재 등급 목록 API 조회
    def load_grades(self):
        if not self.session.user_id:
            return
        try:
            response = requests.get(
                f"{SERVER_URL}/api/admin/grades",
                params={"admin_user_id": self.session.user_id},
                timeout=10,
            )
            if not response.ok:
                QMessageBox.warning(
                    self, "조회 실패",
                    str(response.json().get("detail", "회원등급을 불러올 수 없습니다.")),
                )
                return
            users = response.json().get("users", [])
            self.grade_table.setRowCount(len(users))
            self.grade_rows = []
            grades = ("일반", "비즈니스", "VIP", "VVIP")
            for row, member in enumerate(users):
                self.grade_table.setItem(
                    row, 0, QTableWidgetItem(str(member.get("name", "")))
                )
                self.grade_table.setItem(
                    row, 1, QTableWidgetItem(str(member.get("email", "")))
                )
                self.grade_table.setItem(
                    row, 2, QTableWidgetItem(str(member.get("grade", "일반")))
                )
                combo = QComboBox()
                combo.addItems(grades)
                combo.setCurrentText(str(member.get("grade", "일반")))
                combo.activated.connect(
                    lambda _index, box=combo: box.hidePopup()
                )
                self.grade_table.setCellWidget(row, 3, combo)
                self.grade_rows.append(
                    (int(member["user_id"]), combo, str(member.get("grade", "일반")))
                )
            apply_admin_table_style(self.grade_table)
        except requests.RequestException:
            QMessageBox.warning(self, "연결 오류", "서버에 연결할 수 없습니다.")

    # 변경된 등급만 서버에 저장
    def save_grades(self):
        changed = [
            (user_id, combo.currentText())
            for user_id, combo, old_grade in self.grade_rows
            if combo.currentText() != old_grade
        ]
        if not changed:
            QMessageBox.information(self, "등급 변경", "변경된 등급이 없습니다.")
            return
        try:
            for user_id, grade in changed:
                response = requests.put(
                    f"{SERVER_URL}/api/admin/users/grade",
                    json={
                        "admin_user_id": self.session.user_id,
                        "user_id": user_id,
                        "grade": grade,
                    },
                    timeout=10,
                )
                if not response.ok:
                    QMessageBox.warning(
                        self, "변경 실패",
                        str(response.json().get("detail", "등급을 변경할 수 없습니다.")),
                    )
                    return
            QMessageBox.information(self, "변경 완료", "회원 등급을 변경했습니다.")
            self.load_grades()
        except requests.RequestException:
            QMessageBox.warning(self, "연결 오류", "서버에 연결할 수 없습니다.")


__all__ = ["AdminPage"]
