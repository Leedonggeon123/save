from __future__ import annotations  # 타입 힌트를 지연 평가해 최신 타입 문법과 순환 참조를 안전하게 처리한다.

import sys  # 프로그램 인자와 종료 코드를 사용한다.
import time  # 재연결 시도 사이의 대기 시간을 제어한다.
from datetime import datetime  # 메일 목록의 날짜를 화면 형식으로 변환한다.
from pathlib import Path  # UI 파일 경로를 운영체제와 무관하게 만든다.

from PySide6.QtCore import QObject, QThread, Signal, Slot, QTimer  # Qt 객체·스레드·시그널·타이머를 가져온다.
from PySide6.QtUiTools import QUiLoader  # Qt Designer UI 파일을 읽는 로더다.
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidgetItem, QTextEdit, QVBoxLayout, QHBoxLayout  # 메일 화면에 필요한 위젯과 레이아웃이다.

from client.mail_tcp_client import MailTcpClient


class MailWorker(QObject):
    result = Signal(dict)  # 서버 요청 성공 결과를 UI 스레드로 전달한다.
    failed = Signal(str)  # 오류나 상태 안내 문구를 UI에 전달한다.
    connection_state = Signal(str)  # 연결·재연결·오프라인 상태를 전달한다.

    def __init__(self):
        super().__init__()  # QObject 초기화를 수행한다.
        self.client = MailTcpClient()  # TCP 서버와 통신할 클라이언트를 생성한다.
        self.credentials: tuple[str, str] | None = None  # 재연결에 사용할 최근 로그인 정보를 보관한다.
        self._reconnecting = False  # 중복 재연결 시도를 방지하는 상태값이다.

    @Slot(str, str)
    def login(self, email: str, password: str):
        self.credentials = (email, password)  # 로그인 성공 후 자동 재연결에 사용할 자격 정보를 저장한다.
        self._call(self.client.login, email, password, reconnect=False)  # 최초 로그인은 자동 재연결 없이 요청한다.

    @Slot(object)
    def list_mails(self, request):
        if isinstance(request, str):  # 이전 호출 방식의 문자열 폴더도 지원한다.
            request = {"folder": request}  # 문자열을 요청 딕셔너리로 변환한다.
        self._call(  # 목록 조회를 공통 통신 래퍼로 실행한다.
            self.client.list_mails,
            request.get("folder", "inbox"),  # 조회할 메일함을 전달한다.
            request.get("query", ""),  # 검색어를 전달한다.
            request.get("page", 1),  # 현재 페이지 번호를 전달한다.
            request.get("page_size", 20),  # 페이지당 메일 수를 전달한다.
            read_filter=request.get("read_filter", "all"),  # 읽음 상태 필터를 전달한다.
            sort=request.get("sort", "newest"),  # 정렬 조건을 전달한다.
        )

    @Slot()
    def poll_inbox(self):
        self._call(self.client.list_mails, "inbox", page=1, page_size=100, _purpose="poll_inbox")  # 새 메일 알림용 받은 메일함을 주기적으로 조회한다.

    @Slot(object)
    def send_mail(self, data: dict):
        self._call(self.client.send_mail, data["recipients"], data["subject"], data["body"], data["draft"], data.get("draft_id"))  # 전송 또는 임시 저장 요청을 서버에 보낸다.

    @Slot(object)
    def delete_mail(self, data: dict):
        self._call(self.client.delete_mail, data["mail_id"], data["folder"])  # 단일 메일 삭제 요청을 전달한다.

    @Slot(object)
    def read_mail(self, mail_id):
        self._call(self.client.read_mail, mail_id)  # 메일 읽음 상태 변경 요청을 전달한다.

    @Slot(object)
    def delete_mails(self, mails: list[dict]):
        self._call(self.client.delete_mails, mails)  # 여러 선택 메일 삭제 요청을 전달한다.

    @Slot(object)
    def restore_mails(self, mails: list[dict]):
        self._call(self.client.restore_mails, mails)  # 휴지통 메일 복구 요청을 전달한다.

    @Slot(object)
    def permanently_delete_mails(self, mails: list[dict]):
        self._call(self.client.permanently_delete_mails, mails)  # 휴지통 메일 영구 삭제 요청을 전달한다.

    @Slot()
    def empty_trash(self):
        self._call(self.client.empty_trash)  # 휴지통 전체 비우기 요청을 전달한다.

    @Slot()
    def get_settings(self):
        self._call(self.client.get_settings)  # 사용자 메일 설정 조회 요청을 전달한다.

    @Slot(object)
    def update_settings(self, settings: dict):
        self._call(self.client.update_settings, settings)  # 사용자 메일 설정 저장 요청을 전달한다.

    @Slot()
    def list_blacklist(self):
        self._call(self.client.list_blacklist)  # 블랙리스트 조회 요청을 전달한다.

    @Slot(str)
    def add_blacklist(self, email: str):
        self._call(self.client.add_blacklist, email)  # 블랙리스트 추가 요청을 전달한다.

    @Slot(object)
    def remove_blacklist(self, blocked_id):
        self._call(self.client.remove_blacklist, blocked_id)  # 블랙리스트 삭제 요청을 전달한다.

    def _call(self, function, *args, reconnect: bool = True, _purpose: str | None = None, **kwargs):
        try:
            response = function(*args, **kwargs)  # TCP 클라이언트 함수의 결과를 동기적으로 받는다.
            if _purpose:
                response["_purpose"] = _purpose  # 주기 조회처럼 UI가 구분해야 하는 목적을 결과에 표시한다.
            self.result.emit(response)  # 성공 결과를 UI 스레드에 알린다.
        except Exception as exc:
            if not self._is_connection_error(exc):
                self.failed.emit(str(exc))  # 일반 오류는 재연결 없이 사용자에게 전달한다.
                return  # 현재 요청 처리를 종료한다.
            self.client.close()  # 끊어진 소켓을 닫아 다음 연결을 준비한다.
            self.connection_state.emit("reconnecting")  # UI에 재연결 중 상태를 알린다.
            if reconnect and self._reconnect():
                self.failed.emit("연결이 복구되었습니다. 현재 메일함을 다시 조회합니다.")  # 재연결 성공 안내를 보낸다.
                return  # 현재 실패한 요청은 중복 실행하지 않는다.
            self.connection_state.emit("offline")  # 재연결 실패 상태를 UI에 전달한다.
            self.failed.emit("메일 서버와 연결할 수 없습니다. 서버가 종료되었거나 네트워크 연결이 끊겼습니다.")  # 서버 종료·네트워크 단절 안내를 보여준다.

    @staticmethod
    def _is_connection_error(exc: Exception) -> bool:
        return isinstance(exc, (ConnectionError, OSError, TimeoutError))  # 재연결할 가치가 있는 연결 계열 예외인지 판별한다.

    def _reconnect(self) -> bool:
        if self._reconnecting or not self.credentials:  # 이미 재연결 중이거나 로그인 정보가 없으면 중복 시도를 막는다.
            return False  # 재연결할 수 없음을 반환한다.
        self._reconnecting = True  # 다른 요청이 동시에 재연결하지 못하게 표시한다.
        try:
            email, password = self.credentials  # 저장해 둔 로그인 정보를 꺼낸다.
            for delay in (0.3, 0.8, 1.5):  # 짧은 지수형 대기 간격으로 제한된 횟수만 시도한다.
                time.sleep(delay)  # 서버가 다시 올라올 시간을 준다.
                try:
                    response = self.client.login(email, password)  # 로그인 요청으로 연결과 인증을 함께 복구한다.
                    if response.get("success"):
                        self.connection_state.emit("connected")  # UI에 연결 복구를 알린다.
                        return True  # 재연결 성공을 반환한다.
                except Exception:
                    self.client.close()  # 실패한 재연결 소켓을 닫고 다음 시도를 준비한다.
        finally:
            self._reconnecting = False  # 성공·실패와 관계없이 재연결 잠금을 해제한다.
        return False  # 모든 시도가 실패했음을 반환한다.


class ComposeDialog(QDialog):
    submitted = Signal(dict)  # 보내기·수동 임시 저장 데이터를 부모 화면에 전달한다.
    autosaved = Signal(dict)  # 자동 저장 데이터를 부모 화면에 전달한다.

    def __init__(self, parent=None, sender_email: str = "", settings: dict | None = None, draft: dict | None = None):
        super().__init__(parent)  # 대화상자 기본 초기화를 수행한다.
        self.setWindowTitle("메일 쓰기")  # 창 제목을 설정한다.
        self.resize(520, 430)  # 작성 창의 기본 크기를 지정한다.
        self.setStyleSheet("""  # 입력 위젯과 버튼의 공통 화면 스타일을 지정한다.
            QDialog { background:#f4f7fb; color:#1f2937; }
            QLineEdit, QTextEdit { background:white; border:1px solid #cbd9e5; border-radius:6px; padding:8px; }
            QLineEdit:focus, QTextEdit:focus { border:2px solid #73bde4; padding:7px; }
            QPushButton { background:#ffffff; border:1px solid #cbd9e5; border-radius:6px; padding:8px 14px; }
            QPushButton:hover { background:#edf8fe; }
        """)
        self.sender_edit = QLineEdit(sender_email)  # 현재 로그인한 발신자 이메일을 표시한다.
        self.sender_edit.setReadOnly(True)  # 발신자 변경을 막는다.
        self.settings = settings or {}  # 자동 맞춤 등 저장된 메일 설정을 보관한다.
        self.draft_id = (draft or {}).get("id")  # 기존 임시 메일이면 수정할 ID를 기억한다.
        self._submitted = False  # 제출 또는 닫기 처리 여부를 기록한다.
        self._last_saved_snapshot = None  # 마지막 저장 시점의 내용을 비교하기 위한 값이다.
        self.to_edit = QLineEdit()  # 수신자 입력 필드를 만든다.
        self.to_edit.setPlaceholderText("받는 사람 이메일 (여러 명은 쉼표로 구분)")  # 수신자 입력 방법을 안내한다.
        self.subject_edit = QLineEdit()  # 제목 입력 필드를 만든다.
        self.subject_edit.setMaxLength(255)  # 서버 제목 컬럼 길이에 맞춰 입력을 제한한다.
        self.body_edit = QTextEdit()  # 본문 입력 영역을 만든다.
        self.body_edit.setAcceptRichText(False)  # 서버가 텍스트 본문만 저장하므로 서식을 막는다.
        self.body_edit.setPlaceholderText("메일 내용을 입력하세요. 텍스트만 전송할 수 있습니다.")  # 본문 입력 안내를 표시한다.
        self.body_edit.textChanged.connect(self.enforce_auto_fit_limit)  # 입력마다 자동 맞춤 글자 수 제한을 적용한다.
        if draft:
            self.to_edit.setText(", ".join(draft.get("to", [])))  # 기존 임시 메일의 수신자를 복원한다.
            self.subject_edit.setText(str(draft.get("subject", "")))  # 기존 제목을 복원한다.
            self.body_edit.setPlainText(str(draft.get("body", "")))  # 기존 본문을 복원한다.
        form = QFormLayout()  # 라벨과 입력창을 정렬할 폼 레이아웃을 만든다.
        form.addRow("보내는 사람", self.sender_edit)  # 발신자 행을 추가한다.
        form.addRow("받는 사람", self.to_edit)  # 수신자 행을 추가한다.
        form.addRow("제목", self.subject_edit)  # 제목 행을 추가한다.
        form.addRow("내용", self.body_edit)  # 본문 행을 추가한다.
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)  # 저장·전송·취소 버튼 묶음을 만든다.
        buttons.button(QDialogButtonBox.Save).setText("임시 저장")  # Save 버튼을 한국어로 표시한다.
        buttons.button(QDialogButtonBox.Ok).setText("보내기")  # Ok 버튼을 보내기로 표시한다.
        buttons.button(QDialogButtonBox.Cancel).setText("취소")  # Cancel 버튼을 취소로 표시한다.
        buttons.accepted.connect(lambda: self.submit(False))  # 전송 버튼 클릭을 일반 전송으로 연결한다.
        buttons.rejected.connect(self.close)  # 취소 버튼을 닫기 처리로 연결한다.
        buttons.button(QDialogButtonBox.Save).clicked.connect(lambda: self.submit(True))  # 임시 저장 버튼을 저장 처리로 연결한다.
        layout = QVBoxLayout(self)  # 세로 방향 기본 레이아웃을 만든다.
        layout.addLayout(form)  # 입력 폼을 배치한다.
        layout.addWidget(buttons)  # 하단 버튼을 배치한다.
        if not draft:
            self.apply_auto_fit_settings()  # 새 메일에만 기본 자동 맞춤 문구를 적용한다.
        self._last_saved_snapshot = self._snapshot()  # 초기 내용을 저장 기준으로 기록한다.
        self.autosave_timer = QTimer(self)  # 자동 저장 타이머를 만든다.
        self.autosave_timer.setInterval(30000)  # 30초마다 자동 저장을 시도한다.
        self.autosave_timer.timeout.connect(self.autosave)  # 타이머 만료 시 자동 저장 함수를 호출한다.
        self.autosave_timer.start()  # 자동 저장 타이머를 시작한다.

    def _snapshot(self):
        return (self.to_edit.text(), self.subject_edit.text(), self.body_edit.toPlainText())  # 현재 작성 내용을 비교 가능한 튜플로 만든다.

    def _payload(self):
        recipients = [x.strip() for x in self.to_edit.text().split(",") if x.strip()]  # 콤마로 구분한 수신자를 목록으로 변환한다.
        return {"recipients": recipients, "subject": self.subject_edit.text(), "body": self.body_edit.toPlainText(), "draft": True, "draft_id": self.draft_id}  # 임시 저장 요청 데이터를 만든다.

    def autosave(self):
        if self._submitted or self._snapshot() == self._last_saved_snapshot:  # 제출했거나 변경 사항이 없으면 저장하지 않는다.
            return  # 불필요한 서버 요청을 막는다.
        body = self.body_edit.toPlainText()  # 현재 본문을 읽는다.
        if len(body.encode("utf-8")) > 1024:
            return  # 서버 본문 제한을 넘으면 자동 저장하지 않는다.
        self._last_saved_snapshot = self._snapshot()  # 저장 기준을 최신 내용으로 갱신한다.
        self.autosaved.emit(self._payload())  # 부모 컨트롤러에 자동 저장 요청을 보낸다.

    def closeEvent(self, event):
        if self._submitted or self._snapshot() == self._last_saved_snapshot:  # 저장할 변경 사항이 없으면 바로 닫는다.
            event.accept()  # 닫기 이벤트를 승인한다.
            return  # 추가 확인을 생략한다.
        answer = QMessageBox.question(self, "임시 저장 확인", "저장되지 않은 내용을 임시 보관함에 저장하시겠습니까?", QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)  # 저장되지 않은 내용을 어떻게 처리할지 묻는다.
        if answer == QMessageBox.Save:
            body = self.body_edit.toPlainText()  # 저장 전 본문 길이를 검사한다.
            if len(body.encode("utf-8")) > 1024:
                QMessageBox.warning(self, "입력 제한", "메일 본문은 UTF-8 기준 1,024바이트 이하만 저장할 수 있습니다.")  # 제한 초과를 사용자에게 알린다.
                event.ignore()  # 저장되지 않은 상태로 창을 유지한다.
                return  # 닫기 처리를 중단한다.
            self._last_saved_snapshot = self._snapshot()  # 저장 기준을 갱신한다.
            self.autosaved.emit(self._payload())  # 닫기 전 임시 저장 요청을 보낸다.
            self._submitted = True  # 중복 저장 확인을 방지한다.
            event.accept()  # 창을 닫는다.
        elif answer == QMessageBox.Discard:
            self._submitted = True  # 버린 상태를 기록한다.
            event.accept()  # 변경 내용을 저장하지 않고 닫는다.
        else:
            event.ignore()  # 취소를 선택하면 창을 유지한다.

    def apply_auto_fit_settings(self):
        """저장된 앞 문구·기본 문장·뒤 문구를 새 메일 본문에 적용한다."""
        if not self.settings.get("autoFit", False):
            return  # 자동 맞춤 기능이 꺼져 있으면 본문을 채우지 않는다.
        parts = [  # 설정된 세 문구를 순서대로 준비한다.
            str(self.settings.get("prefixMsg", "")).strip(),
            str(self.settings.get("autoFitSentence", "")).strip(),
            str(self.settings.get("suffixMsg", "")).strip(),
        ]
        default_body = "\n".join(part for part in parts if part)  # 빈 문구를 제외하고 줄바꿈으로 결합한다.
        if default_body:
            self.body_edit.setPlainText(default_body)  # 결합한 기본 문구를 본문에 입력한다.
            self.body_edit.moveCursor(self.body_edit.textCursor().MoveOperation.End)  # 커서를 본문 끝에 둔다.

    def enforce_auto_fit_limit(self):
        """작성 본문이 저장된 자동 맞춤 글자 수를 넘지 않게 제한한다."""
        if getattr(self, "_limiting_text", False):
            return  # 내부에서 텍스트를 다시 설정할 때 재귀 호출을 막는다.
        try:
            limit = int(self.settings.get("autoFitChars", 0) or 0)  # 설정값을 정수로 변환한다.
        except (TypeError, ValueError):
            limit = 0  # 잘못된 설정은 제한 없음으로 처리한다.
        if not self.settings.get("autoFit", False) or limit <= 0:
            return  # 기능이 꺼졌거나 유효한 제한이 없으면 종료한다.
        text = self.body_edit.toPlainText()  # 현재 본문을 읽는다.
        if len(text) > limit:
            self._limiting_text = True  # 텍스트 재설정 중 재귀 호출을 차단한다.
            self.body_edit.setPlainText(text[:limit])  # 제한 길이까지만 본문을 남긴다.
            self.body_edit.moveCursor(self.body_edit.textCursor().MoveOperation.End)  # 커서를 잘린 본문 끝에 둔다.
            self._limiting_text = False  # 재귀 방지 상태를 해제한다.

    def submit(self, draft: bool):
        recipients = [x.strip() for x in self.to_edit.text().split(",") if x.strip()]  # 입력된 수신자 문자열을 목록으로 만든다.
        if not recipients and not draft:
            QMessageBox.warning(self, "확인", "받는 사람을 입력하세요.")  # 일반 전송에는 수신자가 필요함을 알린다.
            return  # 전송을 중단한다.
        body = self.body_edit.toPlainText()  # 전송·저장할 본문을 읽는다.
        if len(body.encode("utf-8")) > 1024:
            QMessageBox.warning(self, "입력 제한", "메일 본문은 UTF-8 기준 1,024바이트 이하만 입력할 수 있습니다.")  # 서버 입력 제한을 사용자에게 알린다.
            return  # 요청을 만들지 않는다.
        if not draft:
            summary = (  # 전송 전 확인 창에 표시할 요약을 만든다.
                "메일을 보내시겠습니까?\n\n"
                f"보내는 사람: {self.sender_edit.text()}\n"
                f"받는 사람: {', '.join(recipients)}\n"
                f"제목: {self.subject_edit.text() or '(제목 없음)'}"
            )
            answer = QMessageBox.question(self, "메일 보내기 전 재확인", summary, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)  # 사용자의 최종 전송 확인을 받는다.
            if answer != QMessageBox.Yes:
                return  # 아니오를 선택하면 전송하지 않는다.
        self._submitted = True  # 중복 제출과 닫기 시 재저장을 막는다.
        self.autosave_timer.stop()  # 제출 후 자동 저장 타이머를 멈춘다.
        self.submitted.emit({"recipients": recipients, "subject": self.subject_edit.text(), "body": body, "draft": draft, "draft_id": self.draft_id})  # 부모에 전송·저장 데이터를 전달한다.
        self.accept()  # 작성 대화상자를 닫는다.


class MailDetailDialog(QDialog):
    """선택한 메일 전체 내용을 읽기 전용으로 보여주는 대화상자다."""

    reply_requested = Signal(dict)  # 답장 버튼에서 원본 메일을 부모 화면으로 전달한다.

    def __init__(self, parent=None, mail: dict | None = None, allow_reply: bool = False):
        super().__init__(parent)  # 대화상자 기본 초기화를 수행한다.
        mail = mail or {}  # 메일 데이터가 없을 때 빈 메일로 처리한다.
        self.setWindowTitle("메일 상세 보기")  # 상세 보기 창 제목을 설정한다.
        self.resize(620, 520)  # 상세 보기 창의 기본 크기를 지정한다.
        self.setStyleSheet("""  # 상세 보기 입력·버튼 스타일을 지정한다.
            QDialog { background:#f4f7fb; color:#1f2937; }
            QLineEdit, QTextEdit { background:white; border:1px solid #cbd9e5; border-radius:6px; padding:8px; }
            QPushButton { background:#2497d0; color:white; border:0; border-radius:6px; padding:8px 16px; }
        """)
        sender = QLineEdit(str(mail.get("from", "")))  # 발신자 표시 필드를 만든다.
        receiver = QLineEdit(", ".join(mail.get("to", [])))  # 수신자 목록을 표시 필드에 넣는다.
        subject = QLineEdit(str(mail.get("subject", "")))  # 제목을 표시한다.
        created_at = QLineEdit(str(mail.get("createdAt", mail.get("created_at", ""))))  # 메일 생성 시각을 표시한다.
        for field in (sender, receiver, subject, created_at):
            field.setReadOnly(True)  # 상세 정보는 수정할 수 없게 한다.
        body = QTextEdit()  # 전체 본문 표시 영역을 만든다.
        body.setReadOnly(True)  # 본문도 읽기 전용으로 설정한다.
        body.setPlainText(str(mail.get("body", "")))  # 선택 메일의 본문을 표시한다.
        form = QFormLayout()  # 메타데이터 배치용 폼 레이아웃을 만든다.
        form.addRow("보낸 사람", sender)  # 발신자 행을 추가한다.
        form.addRow("받는 사람", receiver)  # 수신자 행을 추가한다.
        form.addRow("제목", subject)  # 제목 행을 추가한다.
        form.addRow("보낸 시간", created_at)  # 시각 행을 추가한다.
        close_button = QDialogButtonBox(QDialogButtonBox.Close)  # 닫기 버튼을 만든다.
        close_button.button(QDialogButtonBox.Close).setText("닫기")  # 닫기 버튼을 한국어로 표시한다.
        close_button.rejected.connect(self.reject)  # 닫기 버튼이 대화상자를 종료하게 한다.
        action_layout = QHBoxLayout()  # 답장·닫기 버튼을 가로로 배치한다.
        if allow_reply:
            reply_button = QPushButton("답장")  # 받은 메일에서만 답장 버튼을 만든다.
            reply_button.clicked.connect(lambda: (self.reply_requested.emit(mail), self.accept()))  # 원본 메일을 전달하고 상세 창을 닫는다.
            action_layout.addWidget(reply_button)  # 답장 버튼을 배치한다.
        action_layout.addStretch()  # 버튼을 왼쪽·오른쪽으로 정렬할 여백을 추가한다.
        action_layout.addWidget(close_button)  # 닫기 버튼을 배치한다.
        layout = QVBoxLayout(self)  # 전체 상세 창의 세로 레이아웃을 만든다.
        layout.addLayout(form)  # 메타데이터 폼을 배치한다.
        layout.addWidget(QLabel("메일 내용"))  # 본문 제목을 표시한다.
        layout.addWidget(body)  # 본문 영역을 배치한다.
        layout.addLayout(action_layout)  # 하단 동작 버튼을 배치한다.


class MailWindowController:
    list_folder_requested = Signal(str)  # 메일함 조회 요청을 작업 스레드로 전달한다.
    send_mail_requested = Signal(object)  # 메일 전송·저장 요청을 작업 스레드로 전달한다.

    def __init__(self):
        loader = QUiLoader()  # Qt Designer UI를 읽을 로더를 생성한다.
        ui_path = Path(__file__).resolve().parents[1] / "mail" / "mail_client" / "ui" / "mail_window.ui"
        self.window = loader.load(str(ui_path))  # UI 파일을 실제 위젯 창으로 로드한다.
        self.worker = MailWorker()  # 서버 통신 담당 객체를 만든다.
        self.thread = QThread()  # 통신 작업을 분리할 스레드를 만든다.
        self.worker.moveToThread(self.thread)  # 네트워크 작업 객체를 작업 스레드로 이동한다.
        self.list_folder_requested.connect(self.worker.list_mails)  # 목록 조회 시그널을 worker에 연결한다.
        self.send_mail_requested.connect(self.worker.send_mail)  # 전송 시그널을 worker에 연결한다.
        self.worker.result.connect(self.handle_result)  # 서버 결과를 UI 처리 함수에 연결한다.
        self.worker.failed.connect(self.handle_error)  # 서버 오류를 UI 상태 표시 함수에 연결한다.
        self.thread.start()  # 작업 스레드를 실행한다.
        self.folder = "inbox"  # 현재 메일함 기본값을 설정한다.
        self._connect_ui()  # UI 버튼과 이벤트를 연결한다.

    def _connect_ui(self):
        self.window.allMailButton.clicked.connect(lambda: self.load_folder("all"))  # 전체 메일함 버튼을 연결한다.
        self.window.inboxButton.clicked.connect(lambda: self.load_folder("inbox"))  # 받은 메일 버튼을 연결한다.
        self.window.sentButton.clicked.connect(lambda: self.load_folder("sent"))  # 보낸 메일 버튼을 연결한다.
        self.window.draftButton.clicked.connect(lambda: self.load_folder("drafts"))  # 임시 보관함 버튼을 연결한다.
        self.window.refreshButton.clicked.connect(lambda: self.load_folder(self.folder))  # 새로고침 시 현재 메일함을 다시 조회한다.
        self.window.composeButton.clicked.connect(self.compose)  # 메일 쓰기 버튼을 작성 창에 연결한다.
        self.window.mailTable.cellDoubleClicked.connect(self.read_mail)  # 메일 행 더블클릭을 상세 보기로 연결한다.

    def load_folder(self, folder: str):
        self.folder = folder  # 현재 메일함 상태를 갱신한다.
        self.window.folderTitleLabel.setText({"all": "전체 메일함", "inbox": "받은 메일", "sent": "보낸 메일", "drafts": "임시 보관함"}[folder])  # 화면 제목을 메일함에 맞게 변경한다.
        self.list_folder_requested.emit(folder)  # 작업 스레드에 목록 조회를 요청한다.

    def compose(self):
        dialog = ComposeDialog(self.window)  # 새 메일 작성 대화상자를 만든다.
        dialog.submitted.connect(self.send_mail_requested.emit)  # 작성 결과를 서버 요청 시그널에 연결한다.
        dialog.exec()  # 작성 창을 모달로 표시한다.

    def read_mail(self, row: int, _column: int):
        item = self.window.mailTable.item(row, 0)  # 더블클릭한 행의 제목 셀을 가져온다.
        if item:
            QMessageBox.information(self.window, "메일 상세", item.data(1000) or item.text())  # 저장해 둔 본문 또는 제목을 임시로 표시한다.

    @Slot(dict)
    def handle_result(self, response: dict):
        if response.get("message") == "file received":  # 파일 전송 관련 내부 응답은 화면 처리에서 제외한다.
            return  # 사용자용 상태 메시지를 갱신하지 않는다.
        if response.get("data", {}).get("mails") is not None:
            self.fill_mails(response["data"]["mails"])  # 서버 메일 목록을 표에 출력한다.
        self.window.statusLabel.setText(response.get("message", "처리 완료"))  # 서버 처리 결과를 하단 상태 영역에 표시한다.
        if response.get("success") and response.get("code") == "MAIL_SENT":
            self.load_folder("sent")  # 전송 성공 후 보낸 메일함을 다시 조회한다.
        elif response.get("success") and response.get("code") == "DRAFT_SAVED":
            self.load_folder("drafts")  # 임시 저장 성공 후 임시 보관함을 다시 조회한다.

    def fill_mails(self, mails: list[dict]):
        table = self.window.mailTable  # 메일 목록 테이블 위젯을 참조한다.
        table.setRowCount(0)  # 기존 목록을 비워 중복 표시를 방지한다.
        for mail in mails:  # 서버에서 받은 메일을 한 건씩 표에 추가한다.
            row = table.rowCount()  # 새 행 번호를 계산한다.
            table.insertRow(row)  # 테이블에 빈 행을 추가한다.
            subject = QTableWidgetItem(("● " if not mail.get("read", False) else "") + str(mail.get("subject", "(제목 없음)")))  # 읽지 않은 메일 표시와 제목을 만든다.
            subject.setData(1000, mail.get("body", ""))  # 셀에 전체 본문을 숨겨 저장한다.
            table.setItem(row, 0, subject)  # 제목 셀을 배치한다.
            table.setItem(row, 1, QTableWidgetItem(str(mail.get("from", ""))))  # 발신자 셀을 배치한다.
            raw_created_at = mail.get("created_at", mail.get("createdAt", ""))  # 서버 시각 필드의 두 가지 이름을 지원한다.
            try:
                parsed_created_at = datetime.fromisoformat(str(raw_created_at).replace("Z", "+00:00"))  # ISO 시각 문자열을 날짜 객체로 변환한다.
                formatted_created_at = parsed_created_at.strftime("%Y-%m-%d %H시:%M분")  # 년-월-일 시:분 형식으로 표시한다.
            except ValueError:
                formatted_created_at = str(raw_created_at)[:16]  # 변환 실패 시 원본 앞부분을 안전하게 표시한다.
            table.setItem(row, 2, QTableWidgetItem(formatted_created_at))  # 시간 셀을 배치한다.
        table.resizeColumnsToContents()  # 내용에 맞춰 열 너비를 조정한다.

    @Slot(str)
    def handle_error(self, message: str):
        self.window.statusLabel.setText(f"통신 오류: {message}")  # 통신 오류나 재연결 상태를 화면 하단에 표시한다.

    def show(self):
        self.window.show()  # 메인 메일 창을 화면에 표시한다.
        self.load_folder("all")  # 시작 시 전체 메일함을 조회한다.


def main():
    app = QApplication(sys.argv)  # Qt 애플리케이션 객체를 생성한다.
    controller = MailWindowController()  # 메일 화면 컨트롤러와 통신 스레드를 준비한다.
    controller.show()  # 메인 창을 표시하고 초기 목록을 요청한다.
    sys.exit(app.exec())  # Qt 이벤트 루프를 실행하고 종료 코드를 반환한다.


if __name__ == "__main__":  # 이 파일을 직접 실행할 때만 GUI를 시작한다.
    main()  # 애플리케이션 진입점이다.
