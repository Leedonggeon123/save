from __future__ import annotations  # 타입 힌트를 지연 평가해 Python 버전 호환성을 높인다.

import os  # 서버 주소와 포트를 환경변수에서 읽기 위해 사용한다.
import socket  # TCP 연결 객체와 연결 함수를 사용하기 위해 가져온다.
import threading  # 소켓 송수신을 보호할 Lock을 만들기 위해 사용한다.
import uuid  # 요청마다 고유한 ID를 생성하기 위해 사용한다.
from typing import Any  # 요청 데이터와 응답의 타입 힌트에 사용한다.

from client.tcp_protocol import recv_frame, request_message, send_frame


class MailTcpClient:
    """메일 서버와 JSON 프레임을 주고받는 동기식 TCP 클라이언트."""

    def __init__(self, host: str | None = None, port: int | None = None):
        self.host = host or os.getenv("CLOUD_SERVER_HOST", "127.0.0.1")  # 전달값, 환경변수, 기본값 순서로 서버 주소를 정한다.
        self.port = port or int(os.getenv("CLOUD_SERVER_PORT", "9000"))  # 서버 TCP 포트를 정한다.
        self.sock: socket.socket | None = None  # 현재 연결된 소켓을 저장한다.
        self.session_id: str | None = None  # 로그인 후 받은 세션 ID를 보관한다.
        self._lock = threading.Lock()  # 하나의 소켓에 요청이 겹쳐 쓰이지 않게 한다.

    def connect(self) -> None:
        self.sock = socket.create_connection((self.host, self.port), timeout=10)  # 최대 10초 동안 서버 연결을 시도한다.
        self.sock.settimeout(30)  # 연결 후 요청 응답은 30초 안에 받아야 한다.

    def close(self) -> None:
        if self.sock:  # 연결된 소켓이 있을 때만 닫는다.
            self.sock.close()  # 운영체제 TCP 연결을 종료한다.
            self.sock = None  # 닫힌 소켓을 다시 사용하지 않도록 초기화한다.

    def request(self, message_type: str, **data: Any) -> dict[str, Any]:
        if not self.sock:  # 아직 연결되지 않았으면 요청 전에 연결한다.
            self.connect()
        request_id = str(uuid.uuid4())  # 응답을 요청과 연결할 고유 ID를 만든다.
        message = request_message(message_type, request_id, session_id=self.session_id, **data)  # 프로토콜 형식의 요청 프레임을 만든다.
        with self._lock:  # 동시에 다른 요청이 프레임을 섞지 못하도록 잠근다.
            send_frame(self.sock, message)  # 서버로 길이 정보가 포함된 프레임을 전송한다.
            response, payload = recv_frame(self.sock)  # 서버 응답과 선택적인 바이너리 payload를 받는다.
        response["payload"] = payload  # 상위 계층에서 사용할 수 있도록 payload를 응답에 붙인다.
        if response.get("data", {}).get("session_id"):  # 로그인 응답에 세션 ID가 포함되어 있는지 확인한다.
            self.session_id = response["data"]["session_id"]  # 다음 요청에 사용할 세션 ID를 저장한다.
        return response  # UI/Worker가 success, code, message, data를 처리하도록 반환한다.

    def is_connected(self) -> bool:
        return self.sock is not None  # 소켓 객체가 존재하는지만 빠르게 확인한다.

    def login(self, email: str, password: str) -> dict[str, Any]:
        return self.request("LOGIN_REQUEST", email=email, password=password)  # 이메일과 비밀번호로 로그인한다.

    def list_mails(self, folder: str = "inbox", query: str = "", page: int = 1, page_size: int = 20, read_filter: str = "all", sort: str = "newest") -> dict[str, Any]:
        return self.request("LIST_MAILS", folder=folder, query=query, page=page, page_size=page_size, read_filter=read_filter, sort=sort)  # 폴더, 검색, 페이지 조건으로 목록을 조회한다.

    def read_mail(self, mail_id: int | str) -> dict[str, Any]:
        return self.request("READ_MAIL", mail_id=mail_id)  # 메일 상세 조회와 읽음 처리를 요청한다.

    def delete_mail(self, mail_id: int | str, folder: str = "inbox") -> dict[str, Any]:
        return self.request("DELETE_MAIL", mail_id=mail_id, folder=folder)  # 메일 한 건의 삭제를 요청한다.

    def delete_mails(self, mails: list[dict[str, Any]]) -> dict[str, Any]:
        return self.request("DELETE_MAILS", mails=mails)  # 선택된 여러 메일을 휴지통으로 이동시킨다.

    def restore_mails(self, mails: list[dict[str, Any]]) -> dict[str, Any]:
        return self.request("RESTORE_MAILS", mails=mails)  # 휴지통 메일을 원래 폴더로 복구한다.

    def permanently_delete_mails(self, mails: list[dict[str, Any]]) -> dict[str, Any]:
        return self.request("PERMANENT_DELETE_MAILS", mails=mails)  # 휴지통 메일을 복구 불가능하게 삭제한다.

    def empty_trash(self) -> dict[str, Any]:
        return self.request("EMPTY_TRASH")  # 로그인한 사용자의 휴지통 전체 비우기를 요청한다.

    def send_mail(self, recipients: list[str], subject: str, body: str, draft: bool = False, draft_id: int | str | None = None) -> dict[str, Any]:
        return self.request(  # 임시 저장과 실제 전송을 하나의 공통 메서드로 처리한다.
            "SAVE_DRAFT" if draft else "SEND_MAIL",  # draft 여부에 따라 서버 요청 종류를 선택한다.
            recipients=recipients,  # 수신자 이메일 목록을 전달한다.
            subject=subject,  # 메일 제목을 전달한다.
            body=body,  # 메일 본문을 전달한다.
            draft_id=draft_id,  # 기존 임시 메일이면 수정할 ID를 전달한다.
        )

    def get_settings(self) -> dict[str, Any]:
        return self.request("GET_SETTINGS")  # 현재 사용자 설정을 조회한다.

    def update_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        return self.request("UPDATE_SETTINGS", settings=settings)  # 메일 설정을 서버에 저장한다.

    def list_blacklist(self) -> dict[str, Any]:
        return self.request("LIST_BLACKLIST")  # 블랙리스트 목록을 조회한다.

    def add_blacklist(self, email: str) -> dict[str, Any]:
        return self.request("ADD_BLACKLIST", email=email)  # 지정한 이메일 사용자를 차단한다.

    def remove_blacklist(self, blocked_id: int | str) -> dict[str, Any]:
        return self.request("REMOVE_BLACKLIST", blocked_id=blocked_id)  # 사용자 ID 기준으로 차단을 해제한다.
