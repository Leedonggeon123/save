from __future__ import annotations  # 타입 힌트를 지연 평가해 순환 참조와 최신 타입 문법을 안전하게 처리한다.

import os

import sys  # Qt 애플리케이션 인자와 종료 코드를 사용한다.
from datetime import datetime  # 메일 시각을 화면 표시 형식으로 변환한다.
from pathlib import Path  # UI·이미지 파일 경로를 조합한다.

from PySide6.QtCore import QObject, QThread, Signal, Slot, QSize, Qt, QTimer  # Qt 객체·스레드·시그널·타이머를 가져온다.
from PySide6.QtGui import QPainter, QPixmap  # 탭을 직접 그리거나 로고 이미지를 표시한다.
from PySide6.QtUiTools import QUiLoader  # Qt Designer UI 파일을 읽는다.
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QMessageBox, QTabBar, QTabWidget, QTableWidgetItem, QVBoxLayout, QSizePolicy  # 화면 구성에 필요한 위젯을 가져온다.

try:
    from client.mail_window import ComposeDialog, MailDetailDialog, MailWorker  # 프로젝트 루트 실행 시 공통 메일 UI 클래스를 가져온다.
except ModuleNotFoundError:  # 패키지 모듈 실행 시 대체 import 경로를 사용한다.
    from client.mail_window import ComposeDialog, MailDetailDialog, MailWorker


class HorizontalSideTabBar(QTabBar):
    """왼쪽 탭 위치는 유지하면서 탭 글자를 가로 방향으로 그린다."""

    def __init__(self, parent=None):
        super().__init__(parent)  # QTabBar 기본 초기화를 수행한다.
        self.setUsesScrollButtons(False)  # 탭이 많아도 좌우 스크롤 버튼을 표시하지 않는다.
        self.setExpanding(False)  # 탭이 전체 너비로 강제 확장되지 않게 한다.
        self.setDrawBase(False)  # 기본 탭 바 배경선을 직접 그리기 위해 끈다.

    def tabSizeHint(self, index: int) -> QSize:
        size = super().tabSizeHint(index)  # 기본 글자 크기 기준 탭 크기를 얻는다.
        return QSize(max(145, size.width() + 26), 48)  # 왼쪽 내비게이션에 맞는 고정 높이와 최소 너비를 반환한다.

    def paintEvent(self, event):
        painter = QPainter(self)  # 탭 바를 직접 그릴 화가 객체를 만든다.
        for index in range(self.count()):  # 모든 탭을 순회한다.
            rect = self.tabRect(index)  # 현재 탭의 화면 사각형을 가져온다.
            selected = index == self.currentIndex()  # 현재 선택된 탭인지 확인한다.
            painter.fillRect(rect, "#ffffff" if selected else "#eaf3f9")  # 선택 여부에 따라 배경색을 칠한다.
            if selected:
                painter.fillRect(rect.left(), rect.top(), 4, rect.height(), "#56b4e9")  # 선택 탭 왼쪽에 강조 선을 그린다.
            painter.setPen("#1976b9" if selected else "#5d6b7c")  # 선택 상태에 따른 글자 색을 설정한다.
            font = painter.font()  # 현재 글꼴을 복사한다.
            font.setBold(selected)  # 선택 탭만 굵게 표시한다.
            painter.setFont(font)  # 변경한 글꼴을 적용한다.
            painter.drawText(rect.adjusted(18 if selected else 22, 0, -8, 0), 0x84, self.tabText(index))  # 탭 문구를 가로 방향으로 그린다.


class MailManagementController(QObject):
    login_requested = Signal(str, str)  # 로그인 정보를 작업 스레드로 전달한다.
    folder_requested = Signal(object)  # 메일함·검색·페이지 조회 요청을 전달한다.
    settings_requested = Signal()  # 설정 조회 요청을 전달한다.
    settings_update_requested = Signal(object)  # 설정 저장 요청을 전달한다.
    blacklist_requested = Signal()  # 블랙리스트 조회 요청을 전달한다.
    blacklist_add_requested = Signal(str)  # 블랙리스트 추가 요청을 전달한다.
    blacklist_remove_requested = Signal(object)  # 블랙리스트 삭제 요청을 전달한다.
    send_mail_requested = Signal(object)  # 메일 전송·임시 저장 요청을 전달한다.
    delete_mail_requested = Signal(object)  # 단일 삭제 요청을 전달한다.
    delete_mails_requested = Signal(object)  # 복수 삭제 요청을 전달한다.
    restore_mails_requested = Signal(object)  # 휴지통 복구 요청을 전달한다.
    permanently_delete_mails_requested = Signal(object)  # 영구 삭제 요청을 전달한다.
    empty_trash_requested = Signal()  # 휴지통 비우기 요청을 전달한다.
    poll_inbox_requested = Signal()  # 새 메일 주기 조회 요청을 전달한다.
    read_mail_requested = Signal(object)  # 읽음 처리 요청을 전달한다.

    def __init__(self):
        super().__init__()  # QObject 기본 초기화를 수행한다.
        loader = QUiLoader()  # Qt Designer UI 파일을 읽을 로더를 만든다.
        ui_path = Path(__file__).resolve().parents[1] / "mail" / "mail_client" / "ui" / "mail_management_window.ui"
        self.window = loader.load(str(ui_path))  # UI 파일을 실제 창으로 로드한다.
        if self.window is None:
            raise RuntimeError(f"Could not load UI: {ui_path}")  # UI 로드 실패는 실행을 계속할 수 없으므로 명확히 중단한다.
        # 검색 조건 영역과 20개 메일 목록, 페이지 이동 영역이 서로 겹치지
        # 않도록 기본 창 높이를 확보한다.
        self.window.resize(1150, 850)  # 검색·메일 20개·페이지 영역이 겹치지 않는 기본 크기를 지정한다.
        self.window.setMinimumHeight(820)  # 창을 지나치게 줄여 레이아웃이 깨지는 것을 막는다.
        logo_path = Path(__file__).resolve().parents[1] / "mail" / "mail_client" / "assets" / "jewel_cloud_logo.png"
        if logo_path.exists():
            self.window.logoLabel.setPixmap(QPixmap(str(logo_path)))  # 로고를 화면에 표시한다.
            self.window.logoLabel.setToolTip("Jewel Cloud")  # 로고에 설명 툴팁을 붙인다.
        self._create_settings_window()  # 설정과 블랙리스트를 별도 모달 창으로 구성한다.

        self.worker = MailWorker()  # 서버 통신을 담당하는 worker를 생성한다.
        self.thread = QThread(self)  # UI를 막지 않을 작업 스레드를 만든다.
        self.worker.moveToThread(self.thread)  # 네트워크 작업을 작업 스레드에서 실행하게 한다.
        self.folder_requested.connect(self.worker.list_mails)  # 메일 목록 요청을 worker에 연결한다.
        self.settings_requested.connect(self.worker.get_settings)  # 설정 조회 요청을 연결한다.
        self.settings_update_requested.connect(self.worker.update_settings)  # 설정 저장 요청을 연결한다.
        self.blacklist_requested.connect(self.worker.list_blacklist)  # 블랙리스트 조회 요청을 연결한다.
        self.blacklist_add_requested.connect(self.worker.add_blacklist)  # 블랙리스트 추가 요청을 연결한다.
        self.blacklist_remove_requested.connect(self.worker.remove_blacklist)  # 블랙리스트 삭제 요청을 연결한다.
        self.send_mail_requested.connect(self.worker.send_mail)  # 메일 전송·저장 요청을 연결한다.
        self.delete_mail_requested.connect(self.worker.delete_mail)  # 단일 삭제 요청을 연결한다.
        self.delete_mails_requested.connect(self.worker.delete_mails)  # 복수 삭제 요청을 연결한다.
        self.restore_mails_requested.connect(self.worker.restore_mails)  # 복구 요청을 연결한다.
        self.permanently_delete_mails_requested.connect(self.worker.permanently_delete_mails)  # 영구 삭제 요청을 연결한다.
        self.empty_trash_requested.connect(self.worker.empty_trash)  # 휴지통 비우기 요청을 연결한다.
        self.read_mail_requested.connect(self.worker.read_mail)  # 읽음 처리 요청을 연결한다.
        self.login_requested.connect(self.worker.login)  # 로그인 요청을 연결한다.
        self.poll_inbox_requested.connect(self.worker.poll_inbox)  # 주기 조회 요청을 연결한다.
        self.worker.result.connect(self.handle_result)  # 서버 성공 결과를 UI 처리 함수에 연결한다.
        self.worker.failed.connect(self.handle_error)  # 서버 오류를 UI에 표시하게 연결한다.
        self.worker.connection_state.connect(self.handle_connection_state)  # 재연결 상태를 UI에 반영하게 연결한다.
        self.thread.start()  # 작업 스레드를 시작한다.
        self.folder = "inbox"  # 현재 메일함의 기본값이다.
        self.query = ""  # 현재 검색어를 저장한다.
        self.page = 1  # 현재 페이지 번호를 저장한다.
        self.page_size = 20  # 한 페이지에 표시할 메일 수다.
        self.page_count = 1  # 서버 응답 전 기본 페이지 수다.
        self.current_user_email = ""  # 로그인한 사용자 이메일을 저장한다.
        self.pending_read_mails: dict[int, dict] = {}  # 읽음 처리 응답을 기다리는 메일을 보관한다.
        self.known_inbox_ids: set[int] = set()  # 새 메일 감지를 위한 기존 ID 집합이다.
        self.inbox_poll_initialized = False  # 첫 주기 조회를 이미 완료했는지 나타낸다.
        self.mail_request_pending = False  # 중복 목록 요청을 막는 상태값이다.
        self.poll_request_pending = False  # 중복 새 메일 조회를 막는 상태값이다.
        self.server_notice_shown = False  # 서버 종료 안내 중복 표시를 막는다.
        self.inbox_poll_timer = QTimer(self)  # 새 메일 주기 조회 타이머를 만든다.
        self.inbox_poll_timer.setInterval(5000)  # 5초 간격으로 새 메일을 확인한다.
        self.inbox_poll_timer.timeout.connect(self.poll_inbox)  # 타이머 만료 시 받은 메일을 조회한다.
        self.mail_settings = {
            "autoFit": False,
            "autoFitChars": 0,
            "autoFitSentence": "",
            "prefixMsg": "",
            "suffixMsg": "",
        }
        self._connect_ui()  # 화면 버튼과 이벤트를 연결한다.
        self.window.restoreMailButton.hide()  # 초기에는 휴지통 전용 버튼을 숨긴다.
        self.window.permanentDeleteMailButton.hide()  # 초기에는 영구 삭제 버튼을 숨긴다.
        self.window.emptyTrashButton.hide()  # 초기에는 휴지통 비우기 버튼을 숨긴다.
        self.active_compose_dialog = None  # 현재 작성 중인 창을 추적할 변수다.
        # 메일 표가 페이지 이동 영역까지 확장되지 않도록 높이를 제한한다.
        # 한 페이지의 나머지 메일은 표 내부 세로 스크롤로 확인한다.
        self.window.mailTable.setMinimumHeight(260)
        self.window.mailTable.setMaximumHeight(360)
        self.window.mailTable.setFixedHeight(360)
        self.window.mailTable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_header = self.window.mailTable.verticalHeader()
        row_header.setDefaultSectionSize(24)
        row_header.setFixedWidth(38)
        row_header.setDefaultAlignment(Qt.AlignCenter)
        row_header.setStyleSheet("QHeaderView::section{padding:0px;margin:0px;text-align:center;}")
        self.window.mailTable.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

    def _connect_ui(self):
        for index, value in enumerate(("current", "all", "inbox", "sent", "drafts", "trash")):  # 검색 대상 메일함의 내부 값을 매핑한다.
            self.window.searchFolderCombo.setItemData(index, value)  # 화면 문구와 서버용 폴더 값을 연결한다.
        for index, value in enumerate(("all", "read", "unread")):  # 읽음 필터의 내부 값을 매핑한다.
            self.window.readFilterCombo.setItemData(index, value)  # 전체·읽음·안 읽음 값을 저장한다.
        for index, value in enumerate(("newest", "oldest", "subject_asc", "subject_desc")):  # 정렬 옵션의 내부 값을 매핑한다.
            self.window.sortCombo.setItemData(index, value)  # 서버가 이해하는 정렬명을 저장한다.
        self.window.allMailButton.clicked.connect(lambda: self.load_folder("all"))  # 전체 메일함 버튼을 연결한다.
        self.window.inboxButton.clicked.connect(lambda: self.load_folder("inbox"))  # 받은 메일함 버튼을 연결한다.
        self.window.sentButton.clicked.connect(lambda: self.load_folder("sent"))  # 보낸 메일함 버튼을 연결한다.
        self.window.draftButton.clicked.connect(lambda: self.load_folder("drafts"))  # 임시 보관함 버튼을 연결한다.
        self.window.trashButton.clicked.connect(lambda: self.load_folder("trash"))  # 휴지통 버튼을 연결한다.
        self.window.refreshButton.clicked.connect(lambda: self.load_folder(self.folder))  # 현재 메일함 새로고침을 연결한다.
        self.window.mailSettingsButton.hide()  # 메일 설정은 클라우드 설정 메뉴에서만 연다.
        self.window.searchButton.clicked.connect(self.search_mails)  # 검색 버튼을 연결한다.
        self.window.clearSearchButton.clicked.connect(self.clear_search)  # 검색 초기화 버튼을 연결한다.
        self.window.searchEdit.returnPressed.connect(self.search_mails)  # 검색창 Enter 키를 검색에 연결한다.
        self.window.previousPageButton.clicked.connect(self.previous_page)  # 이전 페이지 버튼을 연결한다.
        self.window.nextPageButton.clicked.connect(self.next_page)  # 다음 페이지 버튼을 연결한다.
        self.window.composeButton.clicked.connect(self.compose)  # 메일 쓰기 버튼을 연결한다.
        self.window.deleteMailButton.clicked.connect(self.delete_mail)  # 삭제 버튼을 연결한다.
        self.window.restoreMailButton.clicked.connect(self.restore_mail)  # 복구 버튼을 연결한다.
        self.window.permanentDeleteMailButton.clicked.connect(self.permanent_delete_mail)  # 영구 삭제 버튼을 연결한다.
        self.window.emptyTrashButton.clicked.connect(self.empty_trash)  # 휴지통 비우기 버튼을 연결한다.
        self.window.mainTabs.currentChanged.connect(self.tab_changed)  # 탭 변경 이벤트를 연결한다.
        self.window.saveSettingsButton.clicked.connect(self.save_settings)  # 설정 저장 버튼을 연결한다.
        self.window.addBlacklistButton.clicked.connect(self.add_blacklist)  # 블랙리스트 추가 버튼을 연결한다.
        self.window.removeBlacklistButton.clicked.connect(self.remove_blacklist)  # 블랙리스트 삭제 버튼을 연결한다.
        self.window.mailTable.cellDoubleClicked.connect(self.read_mail)  # 메일 더블클릭을 열람 처리에 연결한다.

    def _create_settings_window(self):
        """메일 설정·블랙리스트 페이지를 별도 모달 창으로 이동한다."""
        main_tabs = self.window.mainTabs  # 기존 UI에 포함된 탭 위젯을 가져온다.
        self.settings_page = main_tabs.widget(1)  # 메일 설정 페이지를 보관한다.
        self.blacklist_page = main_tabs.widget(2)  # 블랙리스트 페이지를 보관한다.
        main_tabs.removeTab(2)  # 메인 화면에서 블랙리스트 탭을 제거한다.
        main_tabs.removeTab(1)  # 메인 화면에서 메일 설정 탭을 제거한다.
        main_tabs.tabBar().hide()  # 사용자에게 기존 탭 영역을 보이지 않게 한다.

        self.settings_window = QDialog(self.window)  # 설정 전용 대화상자를 생성한다.
        self.settings_window.setWindowTitle("Jewel Cloud - 메일 설정")  # 설정 창 제목을 지정한다.
        self.settings_window.resize(820, 600)  # 설정 창의 기본 크기를 지정한다.
        # 설정 창이 열려 있는 동안 메인 메일 화면을 조작하지 못하게 한다.
        self.settings_window.setModal(True)  # 설정 창이 열리면 뒤의 메일 화면 입력을 막는다.
        self.settings_window.setWindowModality(Qt.ApplicationModal)  # 애플리케이션 전체를 모달 상태로 만든다.
        self.settings_window.setStyleSheet("QDialog{background:#f4f7fb;} QTabWidget::pane{background:white;border:1px solid #dce5ee;border-radius:8px;}")  # 설정 창 스타일을 지정한다.
        layout = QVBoxLayout(self.settings_window)  # 설정 창의 세로 레이아웃을 만든다.
        title = QLabel("메일 설정 및 블랙리스트 관리")  # 설정 창 제목 라벨을 만든다.
        title.setStyleSheet("font-size:22px;font-weight:700;color:#14213d;padding:6px;")  # 제목 스타일을 지정한다.
        layout.addWidget(title)  # 제목을 레이아웃에 배치한다.
        self.settings_tabs = QTabWidget()  # 설정·블랙리스트 전환 탭을 만든다.
        self.settings_tabs.addTab(self.settings_page, "메일 설정")  # 메일 설정 페이지를 추가한다.
        self.settings_tabs.addTab(self.blacklist_page, "블랙리스트 관리")  # 블랙리스트 페이지를 추가한다.
        self.settings_tabs.currentChanged.connect(self.settings_window_tab_changed)  # 설정 탭 전환 시 데이터를 조회한다.
        layout.addWidget(self.settings_tabs)  # 설정 탭을 창에 배치한다.
        # 순서도의 '블랙리스트 추가' 별도 화면으로 진입하도록 인라인 입력란은 숨긴다.
        self.window.blacklistEmailEdit.hide()  # 별도 추가 다이얼로그를 사용하므로 인라인 입력을 숨긴다.
        self.window.addBlacklistButton.setText("블랙리스트 추가")  # 버튼 문구를 순서도 기능명에 맞춘다.

    def settings_window_tab_changed(self, index: int):
        if index == 0:
            self.settings_requested.emit()  # 메일 설정 탭을 열면 최신 설정을 조회한다.
        elif index == 1:
            self.blacklist_requested.emit()  # 블랙리스트 탭을 열면 최신 목록을 조회한다.

    def open_mail_settings(self):
        self.settings_tabs.setCurrentIndex(0)  # 설정 창을 열 때 메일 설정 탭을 기본 선택한다.
        self.settings_window.show()  # 설정 창을 표시한다.
        self.settings_window.raise_()  # 다른 창보다 앞에 배치한다.
        self.settings_window.activateWindow()  # 키보드 입력 포커스를 설정 창에 준다.
        self.settings_requested.emit()  # 표시 직후 최신 설정을 조회한다.

    def poll_inbox(self):
        if not self.current_user_email:
            return  # 로그인 전이나 로그인 창이 열려 있으면 조회하지 않는다.
        if self.poll_request_pending or self.mail_request_pending:
            return  # 기존 요청이 끝나지 않았으면 중복 요청을 막는다.
        self.poll_request_pending = True  # 주기 조회 진행 상태를 기록한다.
        self.poll_inbox_requested.emit()  # worker에 받은 메일 조회를 요청한다.

    def show(self):
        self.window.show()  # 로그인 창 없이 메일 화면만 표시한다.
        if not self.current_user_email:
            self.current_user_email = os.getenv("CLOUD_MAIL_USER", "user@jewel.cloud")
            password = os.getenv("CLOUD_MAIL_PASSWORD", "user1234")
            self.login_requested.emit(self.current_user_email, password)

    def delete_mail(self):
        if self.folder == "trash":
            self.window.statusLabel.setText("휴지통에서는 복구 또는 영구 삭제를 선택하세요.")  # 휴지통에서는 일반 삭제 대신 전용 동작을 안내한다.
            return  # 삭제 처리를 중단한다.
        selected = self.selected_mail_entries()  # 체크된 메일 목록을 수집한다.
        if not selected:
            self.window.statusLabel.setText("삭제할 메일을 선택하세요.")  # 선택 항목이 없음을 알린다.
            return  # 요청을 만들지 않는다.
        answer = QMessageBox.question(self.window, "메일 삭제 경고", f"선택한 메일 {len(selected)}개를 삭제하시겠습니까?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)  # 삭제 전 확인을 받는다.
        if answer == QMessageBox.Yes:
            self.delete_mails_requested.emit(selected)  # 사용자가 확인하면 서버에 삭제를 요청한다.

    def selected_mail_entries(self):
        selected = []  # 선택된 메일 요청 목록을 담는다.
        for row in range(self.window.mailTable.rowCount()):  # 표시된 모든 행을 검사한다.
            checkbox = self.window.mailTable.item(row, 0)  # 첫 번째 열의 선택 상자를 가져온다.
            if checkbox and checkbox.checkState() == Qt.Checked:
                mail_item = self.window.mailTable.item(row, 3)  # 제목 셀에 저장한 메타데이터를 가져온다.
                if mail_item and mail_item.data(1001) is not None:
                    selected.append({"mail_id": mail_item.data(1001), "folder": mail_item.data(1002) or self.folder})  # 서버가 요구하는 ID와 폴더를 추가한다.
        return selected  # 선택된 메일 목록을 반환한다.

    def restore_mail(self):
        if self.folder != "trash":
            self.window.statusLabel.setText("휴지통에서 복구할 메일을 선택하세요.")  # 복구 가능한 위치를 안내한다.
            return  # 복구를 중단한다.
        selected = self.selected_mail_entries()  # 선택된 휴지통 메일을 읽는다.
        if not selected:
            self.window.statusLabel.setText("복구할 메일을 선택하세요.")  # 선택 필요 메시지를 표시한다.
            return  # 요청을 중단한다.
        answer = QMessageBox.question(self.window, "메일 복구 확인", f"선택한 메일 {len(selected)}개를 복구하시겠습니까?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)  # 복구 전 확인을 받는다.
        if answer == QMessageBox.Yes:
            self.restore_mails_requested.emit(selected)  # 확인된 메일을 서버에 복구 요청한다.

    def permanent_delete_mail(self):
        if self.folder != "trash":
            self.window.statusLabel.setText("휴지통에서 영구 삭제할 메일을 선택하세요.")
            return
        selected = self.selected_mail_entries()
        if not selected:
            self.window.statusLabel.setText("영구 삭제할 메일을 선택하세요.")
            return
        answer = QMessageBox.question(self.window, "영구 삭제 확인", f"선택한 메일 {len(selected)}개를 영구 삭제하시겠습니까?\n영구 삭제한 메일은 복구할 수 없습니다.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            self.permanently_delete_mails_requested.emit(selected)

    def tab_changed(self, index: int):
        if index == 1:
            self.settings_requested.emit()  # 메일 설정 탭에 들어가면 설정을 조회한다.
        elif index == 2:
            self.blacklist_requested.emit()  # 블랙리스트 탭에 들어가면 목록을 조회한다.

    def load_folder(self, folder: str):
        if folder != self.folder:
            self.query = ""  # 메일함을 바꾸면 기존 검색어를 초기화한다.
            self.window.searchEdit.clear()  # 검색 입력창을 비운다.
            self.window.searchFolderCombo.setCurrentIndex(0)  # 검색 대상을 현재 메일함으로 되돌린다.
        self.folder = folder  # 현재 메일함을 갱신한다.
        self.page = 1  # 메일함 변경 시 첫 페이지부터 표시한다.
        titles = {"all": "전체 메일함", "inbox": "받은 메일", "sent": "보낸 메일", "drafts": "임시 보관함", "trash": "휴지통"}  # 내부 폴더명과 화면 제목을 매핑한다.
        self.window.folderTitleLabel.setText(titles[folder])  # 메일함 제목을 갱신한다.
        self.window.deleteMailButton.setVisible(folder != "trash")  # 휴지통이 아니면 일반 삭제 버튼을 표시한다.
        self.window.restoreMailButton.setVisible(folder == "trash")  # 휴지통에서만 복구 버튼을 표시한다.
        self.window.permanentDeleteMailButton.setVisible(folder == "trash")  # 휴지통에서만 영구 삭제 버튼을 표시한다.
        self.window.emptyTrashButton.setVisible(folder == "trash")  # 휴지통에서만 전체 비우기 버튼을 표시한다.
        self.request_mail_page()  # 변경된 폴더의 첫 페이지를 요청한다.

    def request_mail_page(self):
        if self.mail_request_pending:
            self.window.statusLabel.setText("메일 목록을 불러오는 중입니다.")  # 중복 요청 중임을 사용자에게 알린다.
            return  # 기존 요청이 끝날 때까지 새 요청을 막는다.
        selected_folder = self.window.searchFolderCombo.currentData()  # 검색 대상 콤보의 내부 값을 읽는다.
        target_folder = self.folder if selected_folder in (None, "current") else str(selected_folder)  # 현재함 또는 지정 폴더를 결정한다.
        self.mail_request_pending = True  # 목록 요청 진행 상태를 기록한다.
        self.folder_requested.emit({  # 서버에 목록 조회 조건을 전달한다.
            "folder": target_folder,
            "query": self.query,
            "page": self.page,
            "page_size": self.page_size,
            "read_filter": self.window.readFilterCombo.currentData() or "all",
            "sort": self.window.sortCombo.currentData() or "newest",
        })

    def search_mails(self):
        self.query = self.window.searchEdit.text().strip()  # 검색어를 읽고 양끝 공백을 제거한다.
        self.page = 1  # 검색 결과는 첫 페이지부터 표시한다.
        self.request_mail_page()  # 새 검색 조건으로 목록을 요청한다.

    def clear_search(self):
        self.window.searchEdit.clear()  # 검색어를 초기화한다.
        self.window.searchFolderCombo.setCurrentIndex(0)  # 검색 폴더를 현재함으로 되돌린다.
        self.window.readFilterCombo.setCurrentIndex(0)  # 읽음 필터를 전체로 되돌린다.
        self.window.sortCombo.setCurrentIndex(0)  # 정렬을 최신순으로 되돌린다.
        self.query = ""  # 내부 검색어도 초기화한다.
        self.page = 1  # 첫 페이지로 돌아간다.
        self.request_mail_page()  # 초기 조건으로 목록을 다시 조회한다.

    def previous_page(self):
        if self.page > 1:
            self.page -= 1  # 페이지 번호를 하나 줄인다.
            self.request_mail_page()  # 이전 페이지를 요청한다.

    def next_page(self):
        if self.page < self.page_count:
            self.page += 1  # 페이지 번호를 하나 늘린다.
            self.request_mail_page()  # 다음 페이지를 요청한다.

    def compose(self):
        sender = self.mail_settings.get("defaultSenderEmail") or self.current_user_email  # 저장된 기본 발신자 또는 로그인 계정을 선택한다.
        dialog = ComposeDialog(self.window, sender, self.mail_settings)  # 새 메일 작성 창을 만든다.
        self.connect_compose_dialog(dialog)  # 전송·자동 저장 이벤트를 연결한다.
        dialog.exec()  # 작성 창을 모달로 표시한다.

    def connect_compose_dialog(self, dialog):
        self.active_compose_dialog = dialog  # 자동 저장 응답에 사용할 현재 작성 창을 기억한다.
        dialog.submitted.connect(self.send_mail_requested.emit)  # 수동 전송·저장 요청을 연결한다.
        dialog.autosaved.connect(self.send_mail_requested.emit)  # 자동 저장 요청을 연결한다.

    def read_mail(self, row: int, _column: int):
        item = self.window.mailTable.item(row, 3)  # 더블클릭한 행의 제목 셀을 가져온다.
        if item:
            mail_id = item.data(1001)  # 숨겨 둔 메일 ID를 읽는다.
            folder = item.data(1002) or self.folder  # 메일의 실제 폴더를 결정한다.
            mail = {  # 상세 보기와 답장에 필요한 메일 데이터를 구성한다.
                "id": mail_id,
                "from": self.window.mailTable.item(row, 1).text(),
                "to": [self.window.mailTable.item(row, 2).text()],
                "subject": item.text().removeprefix("● "),
                "createdAt": self.window.mailTable.item(row, 4).text(),
                "body": item.data(1000) or "",
                "folder": folder,
            }
            if folder == "drafts":
                sender = self.mail_settings.get("defaultSenderEmail") or self.current_user_email  # 임시 메일 작성자의 발신자를 결정한다.
                dialog = ComposeDialog(self.window, sender, self.mail_settings, draft=mail)  # 임시 메일을 이어 쓰는 창을 만든다.
                self.connect_compose_dialog(dialog)  # 저장·전송 이벤트를 연결한다.
                dialog.exec()  # 편집 창을 표시한다.
                return  # 임시 메일 처리 후 일반 상세 보기를 생략한다.
            if folder == "inbox" and mail_id is not None:
                self.pending_read_mails[int(mail_id)] = mail  # 읽음 처리 응답 후 상세 표시할 메일을 저장한다.
                self.read_mail_requested.emit(mail_id)  # 서버에 읽음 상태 변경을 요청한다.
            else:
                self.show_mail_detail(mail, allow_reply=folder == "inbox")  # 받은 메일만 답장 버튼을 허용한다.

    def save_settings(self):
        settings = {  # 화면 입력값을 서버 설정 API 형식으로 모은다.
            "autoFit": self.window.autoFitCheck.isChecked(),
            "autoFitChars": self.window.autoFitCharsEdit.text().strip(),
            "autoFitSentence": self.window.autoFitSentenceEdit.text(),
            "defaultSenderEmail": self.window.defaultSenderEdit.text().strip(),
            "prefixMsg": self.window.prefixEdit.text(),
            "suffixMsg": self.window.suffixEdit.text(),
            "downloadPath": self.window.downloadPathEdit.text().strip(),
            "trashRetentionDays": self.window.trashRetentionEdit.text().strip(),
        }
        self.mail_settings.update(settings)  # 작성 창에 즉시 사용할 로컬 설정도 갱신한다.
        self.settings_update_requested.emit(settings)  # 서버 DB에 설정 저장을 요청한다.

    def empty_trash(self):
        if self.folder != "trash":
            return  # 휴지통 화면이 아니면 작업하지 않는다.
        answer = QMessageBox.question(self.window, "휴지통 비우기 확인", "휴지통의 모든 메일을 영구 삭제하시겠습니까?\n삭제 후에는 복구할 수 없습니다.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)  # 되돌릴 수 없는 작업을 재확인한다.
        if answer == QMessageBox.Yes:
            self.empty_trash_requested.emit()  # 확인 시 서버에 휴지통 비우기를 요청한다.

    def add_blacklist(self):
        dialog = QDialog(self.settings_window)  # 설정 창 위에 추가 전용 다이얼로그를 만든다.
        dialog.setWindowTitle("블랙리스트 추가")  # 다이얼로그 제목을 지정한다.
        dialog.setModal(True)  # 입력이 끝날 때까지 뒤 설정 창을 막는다.
        dialog.resize(420, 150)  # 입력 다이얼로그 크기를 지정한다.
        email_edit = QLineEdit()  # 차단 대상 이메일 입력창을 만든다.
        email_edit.setPlaceholderText("차단할 사용자 이메일을 입력하세요")  # 입력 안내를 표시한다.
        form = QFormLayout(dialog)  # 이메일과 버튼을 배치할 폼 레이아웃을 만든다.
        form.addRow("이메일", email_edit)  # 이메일 입력 행을 추가한다.
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)  # 추가·취소 버튼을 만든다.
        buttons.button(QDialogButtonBox.Ok).setText("추가")  # 확인 버튼 문구를 변경한다.
        buttons.button(QDialogButtonBox.Cancel).setText("취소")  # 취소 버튼 문구를 변경한다.
        buttons.accepted.connect(dialog.accept)  # 추가 버튼은 다이얼로그를 승인한다.
        buttons.rejected.connect(dialog.reject)  # 취소 버튼은 다이얼로그를 닫는다.
        form.addRow(buttons)  # 버튼 행을 배치한다.
        if dialog.exec() != QDialog.Accepted:
            return  # 취소했으면 서버 요청을 만들지 않는다.
        email = email_edit.text().strip()  # 입력된 차단 대상 이메일을 읽는다.
        if not email:
            self.window.blacklistStatusLabel.setText("차단할 이메일을 입력하세요.")  # 빈 입력을 사용자에게 알린다.
            return  # 추가 요청을 중단한다.
        self.blacklist_add_requested.emit(email)  # 서버에 블랙리스트 추가를 요청한다.

    def remove_blacklist(self):
        row = self.window.blacklistTable.currentRow()  # 현재 선택된 블랙리스트 행을 가져온다.
        if row < 0:
            self.window.blacklistStatusLabel.setText("삭제할 사용자를 선택하세요.")  # 선택이 없음을 안내한다.
            return  # 삭제를 중단한다.
        blocked_id = self.window.blacklistTable.item(row, 0).data(1000)  # 이름 셀에 저장한 사용자 ID를 읽는다.
        answer = QMessageBox.question(self.window, "블랙리스트 삭제 확인", "정말로 삭제하시겠습니까?", QMessageBox.Yes | QMessageBox.No)  # 삭제 전 확인을 받는다.
        if answer == QMessageBox.Yes:
            self.blacklist_remove_requested.emit(blocked_id)  # 확인된 차단 관계를 서버에서 삭제한다.

    @Slot(dict)
    def handle_result(self, response: dict):
        if response.get("code") == "LOGIN_SUCCESS":
            self.window.statusLabel.setText("메일을 불러오는 중입니다.")
            self.inbox_poll_initialized = False  # 새 메일 감지 기준을 초기화한다.
            self.known_inbox_ids.clear()  # 이전 로그인 계정의 메일 ID를 제거한다.
            self.inbox_poll_timer.start()  # 실시간 새 메일 조회를 시작한다.
            self.settings_requested.emit()  # 로그인 계정의 설정을 조회한다.
            self.load_folder("all")  # 전체 메일함을 초기 화면으로 연다.
            return  # 로그인 응답 처리를 끝낸다.
        if response.get("code") == "LOGIN_FAILED":
            self.window.statusLabel.setText(response.get("message", "메일 서버 로그인에 실패했습니다."))
            return  # 로그인 실패 처리를 끝낸다.
        if response.get("_purpose") == "poll_inbox":
            self.poll_request_pending = False  # 주기 조회 완료 상태로 되돌린다.
            self.handle_inbox_poll(response)  # 새 메일 여부를 확인한다.
            return  # 주기 조회 응답 처리를 끝낸다.
        if response.get("code") == "MAIL_READ":
            self.handle_mail_read(response)  # 읽음 처리 후 상세 창을 연다.
            return  # 읽음 응답 처리를 끝낸다.
        data = response.get("data") or {}  # 응답 데이터가 없을 때 빈 딕셔너리를 사용한다.
        if data.get("mails") is not None:
            self.mail_request_pending = False  # 목록 요청 완료 상태로 되돌린다.
            total_count = int(data.get("total_count", len(data["mails"])))  # 서버 전체 메일 수를 읽는다.
            self.page = int(data.get("page", self.page))  # 서버가 확정한 현재 페이지를 반영한다.
            self.page_count = max(1, (total_count + self.page_size - 1) // self.page_size)  # 전체 건수로 페이지 수를 계산한다.
            self.fill_mails(data["mails"])  # 메일 행을 테이블에 출력한다.
            self.window.pageLabel.setText(f"{self.page} / {self.page_count} 페이지 (최대 {self.page_size}개, 총 {total_count}개)")  # 페이지 상태를 표시한다.
            self.window.previousPageButton.setEnabled(self.page > 1)  # 첫 페이지가 아니면 이전 버튼을 활성화한다.
            self.window.nextPageButton.setEnabled(self.page < self.page_count)  # 마지막 페이지가 아니면 다음 버튼을 활성화한다.
        if data.get("settings") is not None:
            self.fill_settings(data["settings"])  # 서버 설정을 입력 화면에 반영한다.
        if data.get("blocked") is not None:
            self.fill_blacklist(data["blocked"])  # 서버 블랙리스트를 표에 반영한다.
        if response.get("success") and response.get("code") == "DRAFT_SAVED" and self.active_compose_dialog is not None:
            self.active_compose_dialog.draft_id = data.get("draft_id")  # 새 임시 메일 ID를 작성 창에 저장한다.
        message = response.get("message", "처리 완료")  # 서버 메시지를 기본 상태 문구로 사용한다.
        if response.get("success") and response.get("code") == "MAILS_RESTORED":
            message = f"{message} 원래 받은 메일함 또는 보낸 메일함으로 복구되었습니다."
        self.window.settingsStatusLabel.setText(message)  # 설정 영역 상태 문구를 갱신한다.
        self.window.blacklistStatusLabel.setText(message)  # 블랙리스트 영역 상태 문구를 갱신한다.
        self.window.statusLabel.setText(message)  # 메일 영역 상태 문구를 갱신한다.
        # 메일 전송/임시 저장은 서버 DB 반영 후 현재 목록을 다시 조회해야
        # 화면에 새 메일이 즉시 나타난다.
        if response.get("success") and response.get("code") == "MAILS_DELETED":
            self.load_folder(self.folder)  # 삭제 후 현재 목록을 다시 조회한다.
        elif response.get("success") and response.get("code") in {"MAILS_RESTORED", "MAILS_PERMANENTLY_DELETED"}:
            self.load_folder("trash")  # 복구·영구 삭제 후 휴지통 목록을 갱신한다.
        elif response.get("success") and response.get("code") == "TRASH_EMPTIED":
            self.load_folder("trash")  # 휴지통 비우기 후 빈 목록을 표시한다.
        elif response.get("success") and response.get("code") == "MAIL_SENT":
            # 전송 완료 후 보낸 메일함으로 이동하여 서버의 최신 목록을 표시한다.
            self.load_folder("sent")  # 전송 후 보낸 메일함을 갱신한다.
        elif response.get("success") and response.get("code") in {"DRAFT_SAVED", "DRAFT_UPDATED"}:
            # 임시 저장 완료 후 임시 보관함으로 이동하여 최신 목록을 표시한다.
            self.load_folder("drafts")  # 임시 저장 후 임시 보관함을 갱신한다.
        if response.get("success") and response.get("code") in {"BLACKLIST_ADDED", "BLACKLIST_REMOVED"}:
            self.window.blacklistEmailEdit.clear()  # 숨겨진 인라인 입력값도 초기화한다.
            self.blacklist_requested.emit()  # 블랙리스트 변경 후 최신 목록을 다시 조회한다.

    def handle_inbox_poll(self, response: dict):
        if not response.get("success"):
            return  # 실패한 주기 조회는 새 메일 알림을 만들지 않는다.
        mails = (response.get("data") or {}).get("mails") or []  # 조회된 받은 메일 목록을 가져온다.
        current_ids = {int(mail["id"]) for mail in mails if mail.get("id") is not None}  # 현재 서버 메일 ID 집합을 만든다.
        if not self.inbox_poll_initialized:
            self.known_inbox_ids = current_ids  # 첫 조회 결과를 기준 목록으로 저장한다.
            self.inbox_poll_initialized = True  # 초기화가 끝났음을 기록한다.
            return  # 기존 메일을 새 메일로 잘못 알리지 않는다.
        new_ids = current_ids - self.known_inbox_ids  # 이전에 없던 메일 ID를 계산한다.
        self.known_inbox_ids = current_ids  # 다음 비교를 위해 기준 목록을 갱신한다.
        if not new_ids:
            return  # 새 메일이 없으면 알림을 표시하지 않는다.
        count = len(new_ids)  # 도착한 새 메일 수를 계산한다.
        self.window.statusLabel.setText(f"새 메일 {count}개가 도착했습니다.")  # 상태 영역에 새 메일 수를 표시한다.
        QMessageBox.information(self.window, "NEW_MAIL_NOTIFICATION", f"새 메일 {count}개가 도착했습니다.")  # 팝업으로 실시간 알림을 표시한다.
        if self.folder in {"all", "inbox"}:
            self.request_mail_page()  # 현재 화면이 관련 메일함이면 목록을 자동 갱신한다.

    @Slot(str)
    def handle_connection_state(self, state: str):
        if state == "reconnecting":
            self.mail_request_pending = False  # 재연결 중에는 기존 목록 요청 상태를 해제한다.
            self.poll_request_pending = False  # 재연결 중에는 주기 조회 상태도 해제한다.
            self.window.statusLabel.setText("메일 서버와 연결을 다시 시도하고 있습니다...")  # 재연결 상태를 표시한다.
        elif state == "connected":
            self.server_notice_shown = False  # 다음 연결 끊김 안내를 표시할 수 있도록 초기화한다.
            self.window.statusLabel.setText("서버 연결이 복구되었습니다. 메일함을 새로 조회합니다.")  # 복구 상태를 표시한다.
            self.load_folder(self.folder)  # 연결 복구 후 현재 메일함을 다시 조회한다.
        elif state == "offline":
            self.window.statusLabel.setText("메일 서버가 종료되었거나 연결할 수 없습니다.")  # 오프라인 상태를 표시한다.
            if not self.server_notice_shown:
                self.server_notice_shown = True  # 같은 장애에 대한 팝업 중복 표시를 막는다.
                QMessageBox.warning(self.window, "메일 서버 연결 종료", "메일 서버와 연결할 수 없습니다.\n서버를 다시 실행한 후 새로고침해 주세요.")  # 서버 종료 안내를 표시한다.

    def handle_mail_read(self, response: dict):
        mail_id = response.get("data", {}).get("mail_id")  # 읽음 처리된 메일 ID를 읽는다.
        mail = self.pending_read_mails.pop(int(mail_id), {}) if mail_id is not None else {}  # 대기 중인 상세 데이터를 꺼낸다.
        for row in range(self.window.mailTable.rowCount()):  # 현재 표의 행을 순회한다.
            item = self.window.mailTable.item(row, 3)  # 제목 셀을 가져온다.
            if item and item.data(1001) == mail_id:
                text = item.text()  # 읽지 않음 표시가 포함된 제목을 읽는다.
                if text.startswith("● "):
                    item.setText(text[2:])  # 읽음 처리 후 앞의 점 표시를 제거한다.
                break  # 해당 행을 찾았으므로 반복을 끝낸다.
        self.show_mail_detail(mail, allow_reply=mail.get("folder") == "inbox")  # 받은 메일이면 답장 버튼과 함께 상세 창을 연다.

    def show_mail_detail(self, mail: dict, allow_reply: bool = False):
        dialog = MailDetailDialog(self.window, mail, allow_reply=allow_reply)  # 읽기 전용 상세 대화상자를 만든다.
        if allow_reply:
            dialog.reply_requested.connect(self.reply_to_mail)  # 답장 요청을 답장 작성 함수에 연결한다.
        dialog.exec()  # 상세 창을 모달로 표시한다.

    def reply_to_mail(self, mail: dict):
        sender = self.mail_settings.get("defaultSenderEmail") or self.current_user_email  # 답장 발신자를 결정한다.
        subject = str(mail.get("subject", ""))  # 원본 제목을 가져온다.
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"  # 제목에 답장 접두사가 없으면 추가한다.
        original = str(mail.get("body", ""))  # 원본 본문을 가져온다.
        body = f"\n\n----- 원문 -----\n{original}"  # 답장 본문에 원문을 포함한다.
        draft = {"to": [mail.get("from", "")], "subject": subject, "body": body}  # 답장용 초안 데이터를 만든다.
        dialog = ComposeDialog(self.window, sender, self.mail_settings, draft=draft)  # 답장 작성 창을 만든다.
        self.connect_compose_dialog(dialog)  # 전송·저장 이벤트를 연결한다.
        dialog.exec()  # 답장 작성 창을 표시한다.

    def fill_mails(self, mails: list[dict]):
        table = self.window.mailTable  # 메일 목록 테이블을 가져온다.
        table.setRowCount(0)  # 이전 페이지의 행을 지운다.
        table.scrollToTop()  # 새 페이지를 위에서부터 보여준다.
        # 서버가 구버전이라 전체 목록을 보내는 경우에도 현재 페이지의
        # 구간만 사용한다. 최신 서버가 이미 페이지 단위로 보내면 그대로 사용한다.
        if len(mails) > self.page_size:
            start = (self.page - 1) * self.page_size  # 전체 목록 응답에서 현재 페이지 시작 위치를 계산한다.
            visible_mails = mails[start:start + self.page_size]  # 현재 페이지 구간만 잘라낸다.
        else:
            visible_mails = mails[: self.page_size]  # 이미 페이지 단위 응답이면 최대 페이지 크기만 사용한다.
        for local_row, mail in enumerate(visible_mails):  # 현재 페이지 메일을 한 건씩 출력한다.
            row = table.rowCount()  # 추가할 테이블 행 번호를 계산한다.
            table.insertRow(row)  # 빈 행을 삽입한다.
            global_number = (self.page - 1) * self.page_size + local_row + 1  # 전체 목록 기준 메일 번호를 계산한다.
            table.setVerticalHeaderItem(row, QTableWidgetItem(str(global_number)))  # 행 번호를 표시한다.
            subject = QTableWidgetItem(("● " if not mail.get("read", False) else "") + str(mail.get("subject", "(제목 없음)")))  # 읽지 않음 표시와 제목을 만든다.
            check_item = QTableWidgetItem()  # 선택 상자 셀을 만든다.
            check_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)  # 선택 상자만 조작할 수 있게 한다.
            check_item.setCheckState(Qt.Unchecked)  # 기본 상태는 선택 안 함이다.
            table.setItem(row, 0, check_item)  # 선택 상자를 첫 열에 배치한다.
            subject.setData(1000, mail.get("body", ""))  # 본문을 셀 데이터에 저장한다.
            subject.setData(1001, mail.get("id"))  # 메일 ID를 셀 데이터에 저장한다.
            subject.setData(1002, mail.get("folder", self.folder))  # 메일 폴더를 셀 데이터에 저장한다.
            table.setItem(row, 1, QTableWidgetItem(str(mail.get("from", ""))))  # 발신자 열을 채운다.
            table.setItem(row, 2, QTableWidgetItem(", ".join(mail.get("to", []))))  # 수신자 열을 채운다.
            table.setItem(row, 3, subject)  # 제목 열을 배치한다.
            raw_created_at = mail.get("created_at", mail.get("createdAt", ""))  # 서버 시각 필드를 읽는다.
            table.setItem(row, 4, QTableWidgetItem(self.format_mail_datetime(raw_created_at)))  # 시각을 한국어 표시 형식으로 변환해 배치한다.
        table.resizeColumnsToContents()  # 내용에 맞춰 열 너비를 조정한다.
        table.scrollToTop()  # 출력 완료 후 목록을 위로 이동한다.

    @staticmethod
    def format_mail_datetime(value) -> str:
        """ISO 시각을 YYYY-MM-DD HH시:MM분 형식으로 변환한다."""
        text = str(value or "")  # None을 빈 문자열로 바꿔 안전하게 처리한다.
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))  # ISO 문자열을 날짜 객체로 변환한다.
            return parsed.strftime("%Y-%m-%d %H시:%M분")  # 초·타임존을 제외한 분 단위로 표시한다.
        except ValueError:
            return text[:16] if len(text) >= 16 else text  # 변환 실패 시 원문 일부를 안전하게 표시한다.

    def fill_settings(self, settings: dict):
        self.mail_settings.update(settings)  # 작성 창에서 사용할 로컬 설정을 갱신한다.
        self.window.autoFitCheck.setChecked(bool(settings.get("autoFit", True)))  # 자동 맞춤 체크 상태를 반영한다.
        self.window.autoFitCharsEdit.setText(str(settings.get("autoFitChars", "")))  # 글자 수 제한을 반영한다.
        self.window.autoFitSentenceEdit.setText(str(settings.get("autoFitSentence", "")))  # 기본 문장을 반영한다.
        self.window.defaultSenderEdit.setText(str(settings.get("defaultSenderEmail", "")))  # 기본 발신자를 반영한다.
        self.window.prefixEdit.setText(str(settings.get("prefixMsg", "")))  # 앞 문구를 반영한다.
        self.window.suffixEdit.setText(str(settings.get("suffixMsg", "")))  # 뒤 문구를 반영한다.
        self.window.downloadPathEdit.setText(str(settings.get("downloadPath", "")))  # 다운로드 경로를 반영한다.
        self.window.trashRetentionEdit.setText(str(settings.get("trashRetentionDays", 30)))  # 휴지통 보관 기간을 반영한다.

    def fill_blacklist(self, blocked: list[dict]):
        table = self.window.blacklistTable  # 블랙리스트 테이블을 가져온다.
        table.setRowCount(0)  # 기존 목록을 지운다.
        for user in blocked:  # 차단 사용자 목록을 순회한다.
            row = table.rowCount()  # 새 행 번호를 계산한다.
            table.insertRow(row)  # 빈 행을 추가한다.
            name = QTableWidgetItem(str(user.get("name", "")))  # 사용자 이름 셀을 만든다.
            name.setData(1000, user.get("blocked_id", user.get("id")))  # 삭제에 필요한 사용자 ID를 저장한다.
            table.setItem(row, 0, name)  # 이름 열에 배치한다.
            table.setItem(row, 1, QTableWidgetItem(str(user.get("email", ""))))  # 이메일 열에 배치한다.
        table.resizeColumnsToContents()  # 내용에 맞춰 열 너비를 조정한다.

    @Slot(str)
    def handle_error(self, message: str):
        self.mail_request_pending = False  # 오류 후 새 목록 요청을 허용한다.
        self.poll_request_pending = False  # 오류 후 새 주기 조회를 허용한다.
        self.window.settingsStatusLabel.setText(f"통신 오류: {message}")  # 설정 영역에 오류를 표시한다.
        self.window.blacklistStatusLabel.setText(f"통신 오류: {message}")  # 블랙리스트 영역에 오류를 표시한다.
        self.window.statusLabel.setText(f"통신 오류: {message}")  # 메일 영역에 오류를 표시한다.


class LoginDialog(QDialog):
    loginRequested = Signal(str, str)  # 입력한 이메일·비밀번호를 컨트롤러에 전달한다.

    def __init__(self, parent=None):
        super().__init__(parent)  # 대화상자 기본 초기화를 수행한다.
        self.setWindowTitle("Jewel Cloud 로그인")  # 로그인 창 제목을 설정한다.
        self.setModal(True)  # 로그인 전 뒤 화면 조작을 막는다.
        self.resize(380, 190)  # 로그인 창의 기본 크기를 지정한다.
        self.setStyleSheet("""  # 로그인 창의 입력·버튼 스타일을 지정한다.
            QDialog { background:#f4f7fb; color:#1f2937; }
            QLineEdit { background:white; border:1px solid #cbd9e5; border-radius:6px; padding:8px; }
            QLineEdit:focus { border:2px solid #73bde4; padding:7px; }
            QPushButton { background:#2497d0; color:white; border:0; border-radius:6px; padding:8px 16px; }
            QPushButton:hover { background:#147eb4; }
        """)
        self.emailEdit = QLineEdit("user@jewel.cloud")  # 기본 로그인 이메일 입력값을 제공한다.
        self.passwordEdit = QLineEdit("user1234")  # 테스트용 기본 비밀번호를 제공한다.
        self.passwordEdit.setEchoMode(QLineEdit.Password)  # 비밀번호를 화면에서 가린다.
        self.statusLabel = QLabel("서버 계정으로 로그인하세요.")  # 로그인 상태 안내 라벨을 만든다.
        form = QFormLayout()  # 로그인 입력 배치용 폼을 만든다.
        form.addRow("이메일", self.emailEdit)  # 이메일 입력 행을 추가한다.
        form.addRow("비밀번호", self.passwordEdit)  # 비밀번호 입력 행을 추가한다.
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)  # 로그인·종료 버튼을 만든다.
        buttons.button(QDialogButtonBox.Ok).setText("로그인")  # 확인 버튼 문구를 로그인으로 바꾼다.
        buttons.button(QDialogButtonBox.Cancel).setText("종료")  # 취소 버튼 문구를 종료로 바꾼다.
        buttons.accepted.connect(self.submit)  # 로그인 버튼을 제출 함수에 연결한다.
        buttons.rejected.connect(self.reject)  # 종료 버튼을 대화상자 종료에 연결한다.
        layout = QVBoxLayout(self)  # 로그인 창의 세로 레이아웃을 만든다.
        layout.addLayout(form)  # 입력 폼을 배치한다.
        layout.addWidget(self.statusLabel)  # 상태 라벨을 배치한다.
        layout.addWidget(buttons)  # 하단 버튼을 배치한다.

    def submit(self):
        self.statusLabel.setText("로그인 중...")  # 서버 요청 중임을 표시한다.
        self.loginRequested.emit(self.emailEdit.text().strip(), self.passwordEdit.text())  # 입력값을 로그인 요청으로 전달한다.

    def set_status(self, text: str):
        self.statusLabel.setText(text)  # 서버 응답 오류나 안내 문구를 표시한다.


def main():
    app = QApplication(sys.argv)  # Qt 애플리케이션 객체를 만든다.
    controller = MailManagementController()  # 메일 관리 컨트롤러를 초기화한다.
    controller.show()  # 메인 창과 로그인 창을 표시한다.
    sys.exit(app.exec())  # Qt 이벤트 루프를 실행한다.


if __name__ == "__main__":  # 파일을 직접 실행할 때만 GUI를 시작한다.
    main()  # 애플리케이션 진입점이다.
