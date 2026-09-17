"""Threaded TCP server for mail, settings, and blacklist operations.

It uses the same SQLite database created by the existing FastAPI app:
``../data/jewel_cloud.sqlite3``. Start it from the repository root with
``python -m mail_client.server.mail_tcp_server``.
"""
from __future__ import annotations  # 타입 힌트를 즉시 평가하지 않아 순환 참조와 최신 타입 문법을 안전하게 처리한다.

import hashlib  # 비밀번호 검증용 해시 계산에 사용한다.
import hmac  # 해시 비교를 일정한 시간에 수행해 비교 공격을 줄인다.
import os  # 환경 변수에서 서버 설정을 읽는다.
import secrets  # 로그인 성공 응답의 세션 식별자를 안전하게 생성한다.
import socketserver  # 스레드 기반 TCP 서버를 제공한다.
import sqlite3  # 메일 데이터가 저장된 SQLite DB에 접근한다.
import threading  # 클라이언트별 응답 전송을 보호할 잠금에 사용한다.
from datetime import datetime, timezone  # UTC 기준 메일 삭제 시각을 만든다.
from pathlib import Path  # DB 경로를 운영체제에 맞게 조합한다.

try:
    from common.tcp_protocol import recv_frame, send_frame  # 패키지 내부 실행 시 프레임 송수신 함수를 가져온다.
except ModuleNotFoundError:  # 모듈 경로가 프로젝트 루트 기준일 때의 대체 import 경로다.
    from mail_client.common.tcp_protocol import recv_frame, send_frame  # mail_client 패키지 경로에서 다시 가져온다.

ROOT = Path(__file__).resolve().parents[1]  # server 폴더의 상위인 mail_client 프로젝트 경로를 계산한다.
DB_PATH = Path(os.getenv("CLOUD_DB_PATH", str(ROOT / "data" / "jewel_cloud.sqlite3")))  # 환경 변수 또는 기본 DB 경로를 사용한다.
HOST = os.getenv("CLOUD_SERVER_HOST", "0.0.0.0")  # 모든 네트워크 인터페이스에서 받을 주소를 설정한다.
PORT = int(os.getenv("CLOUD_SERVER_PORT", "9000"))  # 환경 변수의 포트 문자열을 정수 포트로 변환한다.


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()  # 삭제 시각 등 서버 기준 시각을 UTC ISO 문자열로 반환한다.


def db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=30)  # 잠금이 풀릴 때까지 최대 30초 기다리며 DB를 연다.
    connection.row_factory = sqlite3.Row  # 컬럼 이름으로 결과를 읽을 수 있도록 행 형식을 설정한다.
    connection.execute("PRAGMA foreign_keys=ON")  # 외래키 제약조건을 연결마다 활성화한다.
    return connection  # 호출한 기능이 쿼리를 수행할 수 있도록 연결을 반환한다.


def password_ok(value: str, salt: str, digest: str) -> bool:
    actual = hashlib.scrypt(value.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=64).hex()  # 입력 비밀번호를 저장된 방식과 동일하게 해시한다.
    return hmac.compare_digest(actual, digest)  # 계산된 해시와 저장 해시를 안전하게 비교한다.


def response(request_id: str | None, success: bool, code: str, message: str, **data):
    return {"type": "RESPONSE", "request_id": request_id, "success": success, "code": code, "message": message, "data": data}  # 모든 요청에 공통인 응답 봉투를 만든다.


class MailHandler(socketserver.BaseRequestHandler):
    def setup(self):
        self.user_id: int | None = None  # 로그인 전에는 인증된 사용자 ID가 없음을 나타낸다.
        self.send_lock = threading.Lock()  # 한 연결에서 응답 프레임이 섞이지 않도록 잠금을 만든다.
        self.request.settimeout(60)  # 유휴 연결이 무한정 남지 않도록 읽기 제한 시간을 둔다.

    def reply(self, request_id, success, code, message, **data):
        with self.send_lock:  # 같은 클라이언트에 대한 동시 응답을 직렬화한다.
            send_frame(self.request, response(request_id, success, code, message, **data))  # 공통 응답을 TCP 프레임으로 전송한다.

    def handle(self):
        while True:  # 하나의 TCP 연결에서 여러 요청을 계속 처리한다.
            try:
                message, _payload = recv_frame(self.request)  # 다음 JSON 헤더와 선택적 payload를 프레임 단위로 읽는다.
            except (ConnectionError, OSError, ValueError):
                return  # 연결 종료·소켓 오류·잘못된 프레임이면 해당 클라이언트를 종료한다.
            try:
                self.dispatch(message)  # 요청 종류에 맞는 기능으로 분배한다.
            except Exception as exc:
                self.reply(message.get("request_id"), False, "INTERNAL_ERROR", str(exc))  # 예외를 서버 전체가 아닌 해당 요청의 오류로 반환한다.

    def dispatch(self, message: dict):
        request_id = message.get("request_id")  # 클라이언트가 보낸 요청 식별자를 보존한다.
        kind = message.get("type")  # 수행할 API 기능명을 읽는다.
        data = message.get("data") or {}  # 데이터가 없을 때도 안전하게 빈 딕셔너리를 사용한다.

        if kind == "LOGIN_REQUEST":  # 로그인 요청은 인증 전에도 허용한다.
            return self.login(request_id, data)  # 인증을 수행하고 연결에 사용자 ID를 저장한다.
        if self.user_id is None:  # 로그인하지 않은 연결은 보호된 기능을 사용할 수 없다.
            return self.reply(request_id, False, "AUTH_REQUIRED", "로그인이 필요합니다.")  # 인증 필요 오류를 즉시 반환한다.
        if kind == "LIST_MAILS":  # 메일 목록 조회 요청을 처리한다.
            return self.list_mails(
                request_id,
                str(data.get("folder", "inbox")),
                str(data.get("query", "")).strip(),
                data.get("page", 1),
                data.get("page_size", 20),
                str(data.get("read_filter", "all")).strip(),
                str(data.get("sort", "newest")).strip(),
            )
        if kind == "READ_MAIL":  # 메일 읽음 처리 요청을 처리한다.
            return self.read_mail(request_id, data.get("mail_id"))
        if kind == "DELETE_MAIL":  # 단일 메일 삭제 요청을 처리한다.
            return self.delete_mail(request_id, data.get("mail_id"), str(data.get("folder", "inbox")))
        if kind == "DELETE_MAILS":  # 여러 메일 삭제 요청을 처리한다.
            return self.delete_mails(request_id, data.get("mails") or [])
        if kind == "RESTORE_MAILS":  # 휴지통 메일 복구 요청을 처리한다.
            return self.restore_mails(request_id, data.get("mails") or [])
        if kind == "PERMANENT_DELETE_MAILS":  # 휴지통 메일 영구 삭제 요청을 처리한다.
            return self.permanently_delete_mails(request_id, data.get("mails") or [])
        if kind == "EMPTY_TRASH":  # 휴지통 전체 비우기 요청을 처리한다.
            return self.empty_trash(request_id)
        if kind in {"SEND_MAIL", "SAVE_DRAFT"}:  # 일반 전송과 임시 저장을 같은 입력 처리기로 연결한다.
            return self.send_mail(request_id, data, kind == "SAVE_DRAFT")
        if kind == "GET_SETTINGS":  # 사용자 메일 설정 조회 요청을 처리한다.
            return self.get_settings(request_id)
        if kind == "UPDATE_SETTINGS":  # 사용자 메일 설정 변경 요청을 처리한다.
            return self.update_settings(request_id, data.get("settings") or {})
        if kind == "LIST_BLACKLIST":  # 블랙리스트 조회 요청을 처리한다.
            return self.list_blacklist(request_id)
        if kind == "ADD_BLACKLIST":  # 블랙리스트 추가 요청을 처리한다.
            return self.add_blacklist(request_id, str(data.get("email", "")))
        if kind == "REMOVE_BLACKLIST":  # 블랙리스트 삭제 요청을 처리한다.
            return self.remove_blacklist(request_id, data.get("blocked_id"))
        self.reply(request_id, False, "UNKNOWN_REQUEST", f"지원하지 않는 요청입니다: {kind}")  # 등록되지 않은 요청 유형을 거부한다.

    def login(self, request_id, data):
        email = str(data.get("email", "")).lower().strip()  # 이메일을 소문자·공백 제거 형태로 정규화한다.
        password = str(data.get("password", ""))  # 입력된 비밀번호를 문자열로 변환한다.
        connection = db()  # 사용자 조회를 위한 DB 연결을 연다.
        row = connection.execute("SELECT * FROM USER WHERE email=?", (email,)).fetchone()  # 이메일로 사용자 정보를 조회한다.
        connection.close()  # 조회가 끝났으므로 연결을 닫는다.
        if not row or row["is_banned"] or not password_ok(password, row["password_salt"], row["password_hash"]):  # 미존재·차단·비밀번호 오류를 모두 실패로 처리한다.
            return self.reply(request_id, False, "LOGIN_FAILED", "이메일 또는 비밀번호가 올바르지 않습니다.")  # 계정 존재 여부를 노출하지 않고 실패를 응답한다.
        self.user_id = int(row["user_id"])  # 이후 요청에 사용할 인증 사용자 ID를 연결에 기록한다.
        self.reply(request_id, True, "LOGIN_SUCCESS", "로그인 성공", session_id=secrets.token_urlsafe(24), user_id=self.user_id, name=row["name"], grade=row["grade"])  # 클라이언트에 로그인 결과와 표시 정보를 반환한다.

    def list_mails(self, request_id, folder: str, query: str = "", page=1, page_size=20, read_filter: str = "all", sort: str = "newest"):
        connection = db()  # 목록 조회에 사용할 DB 연결을 연다.
        self.purge_expired_trash(connection)  # 조회 전에 보관 기간이 지난 휴지통 메일을 정리한다.
        try:
            page = max(1, int(page))  # 페이지 번호가 1보다 작아지지 않도록 보정한다.
            page_size = min(100, max(1, int(page_size)))  # 한 번에 가져오는 수를 1~100개로 제한한다.
        except (TypeError, ValueError):
            page, page_size = 1, 20  # 잘못된 페이지 입력은 안전한 기본값으로 되돌린다.
        offset = (page - 1) * page_size  # SQL OFFSET에 사용할 시작 위치를 계산한다.
        query_like = f"%{query}%"  # 부분 일치 검색을 위한 LIKE 패턴을 만든다.
        read_filter = read_filter if read_filter in {"all", "read", "unread"} else "all"  # 허용된 읽음 필터만 사용한다.
        sort_sql = {  # 사용자가 선택한 정렬명을 안전한 SQL 조각으로 매핑한다.
            "newest": "created_at DESC",
            "oldest": "created_at ASC",
            "subject_asc": "subject COLLATE NOCASE ASC, created_at DESC",
            "subject_desc": "subject COLLATE NOCASE DESC, created_at DESC",
        }.get(sort, "created_at DESC")  # 알 수 없는 정렬 요청은 최신순을 기본값으로 사용한다.
        if folder == "all":
            # 전체 메일함에는 받은 메일·보낸 메일·임시 보관 메일을 함께 표시한다.
            message_condition = "((m.receiver_id=? AND m.folder='inbox') OR (m.sender_id=? AND m.folder='sent'))"  # 전체함에서 현재 사용자의 받은·보낸 메일만 선택한다.
            message_params = [self.user_id, self.user_id]  # 조건의 두 사용자 ID 값을 바인딩한다.
            draft_condition = "t.sender_id=?"  # 전체함에 본인이 작성한 임시 메일을 포함한다.
            draft_params = [self.user_id]  # 임시 메일 작성자 조건의 값이다.
            if query:
                message_condition += " AND (m.subject LIKE ? OR m.content LIKE ? OR s.email LIKE ? OR r.email LIKE ?)"  # 일반 메일의 검색 대상 필드를 추가한다.
                message_params.extend([query_like] * 4)  # 제목·본문·발신자·수신자에 검색어를 바인딩한다.
                draft_condition += " AND (t.subject LIKE ? OR t.content LIKE ? OR u.email LIKE ? OR t.recipient_emails LIKE ?)"  # 임시 메일 검색 조건을 추가한다.
                draft_params.extend([query_like] * 4)  # 임시 메일의 네 검색 필드에 값을 바인딩한다.
            if read_filter == "read":
                message_condition += " AND m.is_read=1"  # 읽은 메일만 선택한다.
            elif read_filter == "unread":
                message_condition += " AND m.is_read=0"  # 읽지 않은 메일만 선택한다.
                draft_condition += " AND 1=0"  # 임시 메일은 읽음 필터 결과에서 제외한다.
            union_sql = f"""  # 일반 메일과 임시 메일을 같은 목록 구조로 합친다.
                SELECT m.msg_id id, s.email sender_email, r.email receiver_email,
                       m.subject, m.content, m.folder, m.is_read, m.created_at
                FROM MESSAGES m
                JOIN USER s ON s.user_id=m.sender_id
                JOIN USER r ON r.user_id=m.receiver_id
                WHERE {message_condition}
                UNION ALL
                SELECT t.temp_msg_id id, u.email sender_email, t.recipient_emails receiver_email,
                       t.subject, t.content, 'drafts' folder, 1 is_read, t.created_at
                FROM TEMP_MESSAGES t
                JOIN USER u ON u.user_id=t.sender_id
                WHERE {draft_condition}
            """
            combined_params = message_params + draft_params  # UNION SQL에 사용할 파라미터를 순서대로 결합한다.
            count = connection.execute(f"SELECT COUNT(*) FROM ({union_sql}) combined", combined_params).fetchone()[0]  # 페이지 계산용 전체 건수를 조회한다.
            combined_params.extend([page_size, offset])  # LIMIT과 OFFSET 값을 추가한다.
            rows = connection.execute(f"SELECT id, sender_email, receiver_email, subject, content, folder, is_read, created_at FROM ({union_sql}) combined ORDER BY {sort_sql} LIMIT ? OFFSET ?", combined_params).fetchall()  # 현재 페이지의 메일을 조회한다.
        elif folder == "drafts":
            where = "t.sender_id=?"  # 임시 보관함에서는 본인이 저장한 임시 메일만 보여준다.
            params = [self.user_id]  # 작성자 조건에 현재 사용자 ID를 넣는다.
            if query:
                where += " AND (t.subject LIKE ? OR t.content LIKE ? OR u.email LIKE ?)"  # 임시 메일의 제목·본문·작성자 검색 조건이다.
                params.extend([query_like] * 3)  # 세 검색 필드에 검색어를 바인딩한다.
            count = connection.execute(f"SELECT COUNT(*) FROM TEMP_MESSAGES t JOIN USER u ON u.user_id=t.sender_id WHERE {where}", params).fetchone()[0]  # 임시 메일 전체 건수를 계산한다.
            params.extend([page_size, offset])  # 페이지 크기와 시작 위치를 추가한다.
            rows = connection.execute(f"SELECT t.temp_msg_id id, u.email sender_email, t.recipient_emails receiver_email, t.subject, t.content, 'drafts' folder, 1 is_read, t.created_at FROM TEMP_MESSAGES t JOIN USER u ON u.user_id=t.sender_id WHERE {where} ORDER BY t.{sort_sql.replace('created_at', 'created_at')} LIMIT ? OFFSET ?", params).fetchall()  # 임시 메일의 현재 페이지를 조회한다.
        else:
            if folder == "all":
                # 전체 메일함은 받은 메일의 inbox 복사본과 보낸 메일의
                # sent 복사본만 합쳐서 보여 주어 중복 표시를 방지한다.
                condition = "((m.receiver_id=? AND m.folder='inbox') OR (m.sender_id=? AND m.folder='sent'))"  # 전체함의 메일 범위를 정의한다.
                parameters = [self.user_id, self.user_id]  # 받은·보낸 조건에 사용자 ID를 바인딩한다.
            elif folder == "inbox":
                condition = "m.receiver_id=? AND m.folder='inbox'"  # 받은 메일만 선택한다.
                parameters = [self.user_id]  # 수신자 조건에 현재 사용자 ID를 넣는다.
            elif folder == "trash":
                # 휴지통에는 이번 삭제 흐름에서 원래 위치를 저장한 메일만 표시한다.
                # 이전 버전에서 잘못 trash 상태가 된 레코드가 새 휴지통을 오염시키지 않게 한다.
                condition = "(m.receiver_id=? OR m.sender_id=?) AND m.folder='trash' AND m.previous_folder IN ('inbox','sent')"  # 실제 삭제된 받은·보낸 메일만 휴지통에 표시한다.
                parameters = [self.user_id, self.user_id]  # 수신자 또는 발신자 조건에 사용자 ID를 넣는다.
            else:
                condition = "m.sender_id=? AND m.folder='sent'"  # 기본적으로 보낸 메일만 선택한다.
                parameters = [self.user_id]  # 발신자 조건에 현재 사용자 ID를 넣는다.
            if query:
                condition += " AND (m.subject LIKE ? OR m.content LIKE ? OR s.email LIKE ? OR r.email LIKE ?)"  # 메일 검색 조건을 추가한다.
                parameters.extend([query_like] * 4)  # 네 검색 필드에 같은 검색어를 바인딩한다.
            if read_filter == "read":
                condition += " AND m.is_read=1"  # 읽은 메일만 남긴다.
            elif read_filter == "unread":
                condition += " AND m.is_read=0"  # 읽지 않은 메일만 남긴다.
            count = connection.execute(f"SELECT COUNT(*) FROM MESSAGES m JOIN USER s ON s.user_id=m.sender_id JOIN USER r ON r.user_id=m.receiver_id WHERE {condition}", parameters).fetchone()[0]  # 필터 적용 후 전체 건수를 계산한다.
            parameters.extend([page_size, offset])  # 페이지 조회에 사용할 LIMIT·OFFSET을 추가한다.
            rows = connection.execute(f"SELECT m.msg_id id, s.email sender_email, r.email receiver_email, m.subject, m.content, m.folder, m.is_read, m.created_at FROM MESSAGES m JOIN USER s ON s.user_id=m.sender_id JOIN USER r ON r.user_id=m.receiver_id WHERE {condition} ORDER BY m.{sort_sql.replace('created_at', 'created_at')} LIMIT ? OFFSET ?", parameters).fetchall()  # 현재 페이지의 일반 메일을 조회한다.
        connection.close()  # 목록 조회가 끝났으므로 DB 연결을 닫는다.
        mails = [{"id": row["id"], "from": row["sender_email"], "to": [address.strip() for address in str(row["receiver_email"] or "").split(",") if address.strip()], "subject": row["subject"], "body": row["content"], "folder": row["folder"], "read": bool(row["is_read"]), "createdAt": row["created_at"]} for row in rows]  # DB 행을 클라이언트 응답 형식으로 변환한다.
        self.reply(request_id, True, "MAIL_LIST", "메일 목록을 불러왔습니다.", mails=mails, total_count=count, page=page, page_size=page_size, query=query)  # 목록과 페이지 정보를 클라이언트에 전송한다.

    def read_mail(self, request_id, mail_id):
        connection = db()  # 메일 열람용 DB 연결을 연다.
        row = connection.execute("SELECT * FROM MESSAGES WHERE msg_id=? AND receiver_id=?", (mail_id, self.user_id)).fetchone()  # 현재 사용자가 받은 메일인지 확인한다.
        if not row:
            connection.close()  # 대상이 없으면 연결을 닫고 종료한다.
            return self.reply(request_id, False, "MAIL_NOT_FOUND", "메일을 찾을 수 없습니다.")  # 존재하지 않거나 권한 없는 메일을 숨긴다.
        connection.execute("UPDATE MESSAGES SET is_read=1 WHERE msg_id=?", (mail_id,))  # 메일을 읽음 상태로 변경한다.
        connection.commit(); connection.close()  # 변경을 확정하고 DB 연결을 닫는다.
        self.reply(request_id, True, "MAIL_READ", "메일을 읽었습니다.", mail_id=mail_id)  # 읽음 처리 결과를 반환한다.

    def delete_mail(self, request_id, mail_id, folder: str):
        connection = db()  # 단일 삭제를 위한 DB 연결을 연다.
        if folder == "drafts":
            cursor = connection.execute("DELETE FROM TEMP_MESSAGES WHERE temp_msg_id=? AND sender_id=?", (mail_id, self.user_id))  # 본인이 작성한 임시 메일을 삭제한다.
        elif folder == "trash":
            cursor = connection.execute("UPDATE MESSAGES SET folder='trash' WHERE 1=0")  # 휴지통 메일은 단일 삭제 대상이 아니므로 아무 것도 변경하지 않는다.
        elif folder == "sent":
            cursor = connection.execute("UPDATE MESSAGES SET previous_folder=folder,folder='trash',deleted_at=? WHERE msg_id=? AND sender_id=? AND folder='sent'", (utc(), mail_id, self.user_id))  # 보낸 메일의 원래 위치를 기록하고 휴지통으로 이동한다.
        else:
            cursor = connection.execute("UPDATE MESSAGES SET previous_folder=folder,folder='trash',deleted_at=? WHERE msg_id=? AND receiver_id=? AND folder='inbox'", (utc(), mail_id, self.user_id))  # 받은 메일을 휴지통으로 이동한다.
        connection.commit(); connection.close()  # 변경을 저장하고 연결을 닫는다.
        if cursor.rowcount == 0:
            return self.reply(request_id, False, "MAIL_NOT_FOUND", "삭제할 메일을 찾을 수 없습니다.")  # 대상이 없거나 권한이 없으면 실패를 반환한다.
        self.reply(request_id, True, "MAIL_DELETED", "메일을 삭제했습니다.")  # 삭제 성공을 알린다.

    def delete_mails(self, request_id, mails: list[dict]):
        connection = db()  # 일괄 삭제용 DB 연결을 연다.
        deleted = 0  # 실제 변경된 메일 수를 누적한다.
        for entry in mails:  # 클라이언트가 선택한 메일을 하나씩 처리한다.
            mail_id = entry.get("mail_id")  # 선택 메일의 식별자를 읽는다.
            folder = str(entry.get("folder", "inbox"))  # 메일함 정보를 읽고 기본값은 받은 메일함으로 둔다.
            if folder == "drafts":
                cursor = connection.execute("DELETE FROM TEMP_MESSAGES WHERE temp_msg_id=? AND sender_id=?", (mail_id, self.user_id))
            elif folder == "trash":
                cursor = connection.execute("UPDATE MESSAGES SET folder='trash' WHERE 1=0")
            elif folder == "sent":
                cursor = connection.execute("UPDATE MESSAGES SET previous_folder=folder,folder='trash',deleted_at=? WHERE msg_id=? AND sender_id=? AND folder='sent'", (utc(), mail_id, self.user_id))
            else:
                cursor = connection.execute("UPDATE MESSAGES SET previous_folder=folder,folder='trash',deleted_at=? WHERE msg_id=? AND receiver_id=? AND folder='inbox'", (utc(), mail_id, self.user_id))
            deleted += max(cursor.rowcount, 0)
        connection.commit()  # 일괄 변경을 한 번에 확정한다.
        connection.close()  # DB 연결을 닫는다.
        if not mails:
            return self.reply(request_id, False, "NO_MAIL_SELECTED", "삭제할 메일을 선택하세요.")  # 선택 항목이 없으면 작업을 거부한다.
        self.reply(request_id, True, "MAILS_DELETED", f"메일 {deleted}개를 삭제했습니다.", deleted_count=deleted)  # 삭제된 개수를 반환한다.

    def restore_mails(self, request_id, mails: list[dict]):
        connection = db()  # 복구 작업용 DB 연결을 연다.
        restored = 0  # 복구된 메일 수를 센다.
        for entry in mails:  # 선택한 휴지통 메일을 순회한다.
            cursor = connection.execute("UPDATE MESSAGES SET folder=CASE WHEN previous_folder IN ('inbox','sent') THEN previous_folder ELSE 'inbox' END, previous_folder='', deleted_at=NULL WHERE msg_id=? AND folder='trash' AND (sender_id=? OR receiver_id=?)", (entry.get("mail_id"), self.user_id, self.user_id))  # 삭제 전 폴더로 되돌리고 삭제 표시를 지운다.
            restored += max(cursor.rowcount, 0)  # 실제 복구된 행 수만 누적한다.
        connection.commit(); connection.close()  # 복구 내용을 저장하고 연결을 닫는다.
        self.reply(request_id, True, "MAILS_RESTORED", f"메일 {restored}개를 복구했습니다.", restored_count=restored)  # 복구 결과를 반환한다.

    def permanently_delete_mails(self, request_id, mails: list[dict]):
        connection = db()  # 영구 삭제 작업용 DB 연결을 연다.
        deleted = 0  # 영구 삭제된 행 수를 누적한다.
        for entry in mails:  # 선택한 휴지통 메일을 순회한다.
            cursor = connection.execute("DELETE FROM MESSAGES WHERE msg_id=? AND folder='trash' AND previous_folder IN ('inbox','sent') AND (sender_id=? OR receiver_id=?)", (entry.get("mail_id"), self.user_id, self.user_id))  # 권한이 있는 휴지통 메일만 DB에서 완전히 삭제한다.
            deleted += max(cursor.rowcount, 0)  # 실제 삭제된 수를 누적한다.
        connection.commit(); connection.close()  # 삭제를 확정하고 연결을 닫는다.
        self.reply(request_id, True, "MAILS_PERMANENTLY_DELETED", f"메일 {deleted}개를 영구 삭제했습니다.", deleted_count=deleted)  # 영구 삭제 결과를 반환한다.

    def purge_expired_trash(self, connection):
        row = connection.execute("SELECT trash_retention_days FROM USER_SETTINGS WHERE user_id=?", (self.user_id,)).fetchone()  # 사용자별 휴지통 보관 기간을 읽는다.
        try:
            days = max(1, int(row[0] if row else 30))  # 최소 1일 이상의 정수 기간으로 보정한다.
        except (TypeError, ValueError):
            days = 30  # 설정이 잘못되면 30일을 기본값으로 사용한다.
        connection.execute("DELETE FROM MESSAGES WHERE folder='trash' AND previous_folder IN ('inbox','sent') AND deleted_at IS NOT NULL AND deleted_at < datetime('now', ? ) AND (sender_id=? OR receiver_id=?)", (f"-{days} days", self.user_id, self.user_id))  # 보관 기간이 지난 휴지통 메일을 자동 삭제한다.
        connection.commit()  # 자동 정리 결과를 확정한다.

    def empty_trash(self, request_id):
        connection = db()  # 휴지통 비우기용 DB 연결을 연다.
        cursor = connection.execute("DELETE FROM MESSAGES WHERE folder='trash' AND previous_folder IN ('inbox','sent') AND (sender_id=? OR receiver_id=?)", (self.user_id, self.user_id))  # 현재 사용자가 접근 가능한 휴지통 메일을 모두 삭제한다.
        connection.commit(); connection.close()  # 영구 삭제를 확정하고 연결을 닫는다.
        self.reply(request_id, True, "TRASH_EMPTIED", f"휴지통을 비웠습니다. {max(cursor.rowcount, 0)}개가 삭제되었습니다.", deleted_count=max(cursor.rowcount, 0))  # 삭제 개수를 응답한다.

    def send_mail(self, request_id, data, draft: bool):
        subject = str(data.get("subject", "(제목 없음)"))[:255]  # 제목을 문자열로 만들고 DB 컬럼 길이에 맞춘다.
        body = str(data.get("body", ""))  # 본문을 문자열로 정규화한다.
        if len(body.encode("utf-8")) > 1024:
            return self.reply(request_id, False, "MESSAGE_TOO_LARGE", "메일 본문은 1024바이트 이하만 사용할 수 있습니다.")  # 저장 스키마 한도를 넘는 본문을 거부한다.
        connection = db()  # 전송 또는 임시 저장에 사용할 DB 연결을 연다.
        if draft:
            recipients = data.get("recipients", [])  # 임시 메일의 수신자 입력을 읽는다.
            if isinstance(recipients, str):
                recipients = [x.strip() for x in recipients.split(",") if x.strip()]  # 콤마로 입력된 문자열을 목록으로 변환한다.
            recipient_emails = ", ".join(str(email).strip().lower() for email in recipients if str(email).strip())  # 수신자 목록을 저장 가능한 문자열로 만든다.
            draft_id = data.get("draft_id")  # 기존 임시 메일 수정 여부를 확인한다.
            if draft_id:
                cursor = connection.execute("UPDATE TEMP_MESSAGES SET recipient_emails=?,content=?,subject=?,created_at=? WHERE temp_msg_id=? AND sender_id=?", (recipient_emails, body, subject, utc(), draft_id, self.user_id))  # 본인이 작성한 임시 메일을 갱신한다.
                if cursor.rowcount == 0:
                    connection.close()  # 대상이 없으면 연결을 정리한다.
                    return self.reply(request_id, False, "DRAFT_NOT_FOUND", "수정할 임시 메일을 찾을 수 없습니다.")  # 다른 사용자의 임시 메일 수정을 막는다.
                connection.commit(); connection.close()  # 수정 내용을 저장하고 연결을 닫는다.
                return self.reply(request_id, True, "DRAFT_UPDATED", "임시 메일을 수정했습니다.")  # 수정 성공을 반환한다.
            cursor = connection.execute("INSERT INTO TEMP_MESSAGES(sender_id,recipient_emails,content,subject,created_at) VALUES(?,?,?,?,?)", (self.user_id, recipient_emails, body, subject, utc()))  # 새 임시 메일을 저장한다.
            connection.commit(); connection.close()  # 임시 저장을 확정하고 연결을 닫는다.
            return self.reply(request_id, True, "DRAFT_SAVED", "임시 보관함에 저장했습니다.", draft_id=cursor.lastrowid)  # 새 임시 메일 ID를 반환한다.
        recipients = data.get("recipients", [])  # 일반 메일의 수신자 목록을 읽는다.
        if isinstance(recipients, str):
            recipients = [x.strip() for x in recipients.split(",") if x.strip()]  # 문자열 수신자를 콤마 기준 목록으로 변환한다.
        sent = []  # 실제 전송된 수신자 이메일을 기록한다.
        skipped = []  # 전송하지 못한 수신자를 기록한다.
        for email in recipients:  # 각 수신자를 검증하고 메일을 생성한다.
            normalized_email = str(email).strip().lower()  # 수신자 이메일을 비교 가능한 형태로 정규화한다.
            target = connection.execute("SELECT user_id,email FROM USER WHERE email=?", (normalized_email,)).fetchone()  # 등록된 수신자 계정을 조회한다.
            if not target or target["user_id"] == self.user_id:
                skipped.append(normalized_email)  # 미등록 사용자나 자기 자신은 전송 대상에서 제외한다.
                continue  # 다음 수신자로 넘어간다.
            blocked = connection.execute("SELECT 1 FROM BLACKLIST WHERE (blocker_id=? AND blocked_id=?) OR (blocker_id=? AND blocked_id=? )", (self.user_id, target["user_id"], target["user_id"], self.user_id)).fetchone()  # 어느 한쪽이 다른 쪽을 차단했는지 확인한다.
            if blocked:
                skipped.append(normalized_email)  # 차단 관계가 있으면 수신자를 제외한다.
                continue  # 차단된 수신자의 처리를 끝낸다.
            now = utc()  # 보낸 메일과 받은 메일에 동일한 전송 시각을 사용한다.
            connection.execute("INSERT INTO MESSAGES(sender_id,receiver_id,content,subject,folder,created_at) VALUES(?,?,?,?,?,?)", (self.user_id, target["user_id"], body, subject, "sent", now))  # 발신자 메일함용 레코드를 만든다.
            connection.execute("INSERT INTO MESSAGES(sender_id,receiver_id,content,subject,folder,created_at) VALUES(?,?,?,?,?,?)", (self.user_id, target["user_id"], body, subject, "inbox", now))  # 수신자 메일함용 레코드를 만든다.
            sent.append(target["email"])  # 성공한 수신자를 응답 목록에 추가한다.
        if sent and data.get("draft_id"):
            connection.execute("DELETE FROM TEMP_MESSAGES WHERE temp_msg_id=? AND sender_id=?", (data.get("draft_id"), self.user_id))  # 임시 메일에서 전송된 초안을 제거한다.
        connection.commit(); connection.close()  # 전송·초안 삭제를 함께 확정한다.
        if not sent:
            return self.reply(
                request_id,
                False,
                "NO_VALID_RECIPIENTS",
                "등록된 사용자이거나 차단되지 않은 수신자가 없어 메일을 저장하지 않았습니다.",
                skipped=skipped,  # 전송 제외된 수신자 목록을 함께 알려준다.
            )
        self.reply(request_id, True, "MAIL_SENT", "메일을 보냈습니다.", recipients=sent)  # 전송 성공 수신자 목록을 반환한다.

    def get_settings(self, request_id):
        connection = db(); row = connection.execute("SELECT * FROM USER_SETTINGS WHERE user_id=?", (self.user_id,)).fetchone(); connection.close()  # 현재 사용자의 설정을 조회하고 연결을 닫는다.
        settings = {"autoFit": bool(row["auto_fit"]), "autoFitChars": row["auto_fit_chars"] or 0, "autoFitSentence": row["auto_fit_sentence"] or "", "defaultSenderEmail": row["default_sender_email"] or "", "prefixMsg": row["prefix_msg"] or "", "suffixMsg": row["suffix_msg"] or "", "downloadPath": row["download_path"] or "", "trashRetentionDays": row["trash_retention_days"] or 30} if row else {}  # DB 컬럼명을 클라이언트 설정 형식으로 변환한다.
        self.reply(request_id, True, "SETTINGS_LOADED", "메일 설정을 불러왔습니다.", settings=settings)  # 설정 데이터를 응답한다.

    def update_settings(self, request_id, settings):
        try:
            auto_fit_chars = max(0, int(settings.get("autoFitChars", 0) or 0))  # 자동 맞춤 글자 수를 0 이상 정수로 변환한다.
        except (TypeError, ValueError):
            return self.reply(request_id, False, "INVALID_SETTINGS", "자동 맞춤 글자 수는 숫자로 입력하세요.")
        try:
            retention_days = max(1, int(settings.get("trashRetentionDays", 30) or 30))  # 휴지통 보관 기간을 최소 1일로 보정한다.
        except (TypeError, ValueError):
            return self.reply(request_id, False, "INVALID_SETTINGS", "휴지통 보관 기간은 숫자로 입력하세요.")
        connection = db(); connection.execute("UPDATE USER_SETTINGS SET auto_fit=?,auto_fit_chars=?,auto_fit_sentence=?,default_sender_email=?,prefix_msg=?,suffix_msg=?,download_path=?,trash_retention_days=? WHERE user_id=?", (int(bool(settings.get("autoFit", True))), auto_fit_chars, settings.get("autoFitSentence", ""), settings.get("defaultSenderEmail", ""), settings.get("prefixMsg", ""), settings.get("suffixMsg", ""), settings.get("downloadPath", ""), retention_days, self.user_id)); connection.commit(); connection.close()  # 검증한 설정을 저장하고 연결을 닫는다.
        self.reply(request_id, True, "SETTINGS_UPDATED", "메일 설정을 저장했습니다.")  # 설정 저장 성공을 응답한다.

    def list_blacklist(self, request_id):
        connection = db(); rows = connection.execute("SELECT b.blocked_id, u.name, u.email FROM BLACKLIST b JOIN USER u ON u.user_id=b.blocked_id WHERE b.blocker_id=?", (self.user_id,)).fetchall(); connection.close()  # 현재 사용자가 등록한 차단 목록을 조회한다.
        self.reply(request_id, True, "BLACKLIST_LIST", "블랙리스트를 불러왔습니다.", blocked=[dict(row) for row in rows])  # 행을 딕셔너리 목록으로 변환해 반환한다.

    def add_blacklist(self, request_id, email):
        email = str(email).strip().lower()  # 차단할 이메일을 정규화한다.
        connection = db(); target = connection.execute("SELECT user_id FROM USER WHERE email=?", (email,)).fetchone()  # 대상 계정이 실제로 존재하는지 확인한다.
        if not target:
            connection.close(); return self.reply(request_id, False, "USER_NOT_FOUND", "해당 사용자를 찾을 수 없습니다.")  # 존재하지 않는 계정은 차단할 수 없다.
        if target["user_id"] == self.user_id:
            connection.close(); return self.reply(request_id, False, "SELF_BLOCK", "본인은 차단할 수 없습니다.")  # 자기 자신을 차단하는 관계를 막는다.
        connection.execute("INSERT OR IGNORE INTO BLACKLIST(blocker_id,blocked_id) VALUES(?,?)", (self.user_id, target["user_id"]))  # 중복 없이 차단 관계를 저장한다.
        connection.commit(); connection.close()  # 블랙리스트 변경을 확정하고 연결을 닫는다.
        self.reply(request_id, True, "BLACKLIST_ADDED", "블랙리스트에 추가했습니다.")  # 추가 성공을 응답한다.

    def remove_blacklist(self, request_id, blocked_id):
        connection = db(); connection.execute("DELETE FROM BLACKLIST WHERE blocker_id=? AND blocked_id=?", (self.user_id, blocked_id)); connection.commit(); connection.close()  # 현재 사용자가 만든 차단 관계만 삭제한다.
        self.reply(request_id, True, "BLACKLIST_REMOVED", "블랙리스트에서 삭제했습니다.")  # 삭제 완료를 응답한다.


class MailTcpServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True  # 서버 재시작 시 기존 소켓 주소를 재사용한다.
    daemon_threads = True  # 메인 서버가 종료되면 작업 스레드도 함께 종료되게 한다.


def main():
    try:
        from database.init_db import initialize  # 프로젝트 루트 기준 실행에서 초기화 함수를 가져온다.
    except ModuleNotFoundError:
        from mail_client.database.init_db import initialize  # 패키지 모듈 실행 시 대체 경로를 사용한다.
    initialize(DB_PATH)  # 서버 시작 전에 DB와 최신 스키마를 준비한다.
    with MailTcpServer((HOST, PORT), MailHandler) as server:  # 서버 리소스를 자동 정리할 수 있도록 컨텍스트로 연다.
        print(f"Mail TCP server listening on {HOST}:{PORT}")  # 운영자가 바인딩 주소와 포트를 확인할 수 있게 출력한다.
        server.serve_forever()  # 종료 신호가 올 때까지 클라이언트 요청을 받는다.


if __name__ == "__main__":  # 이 파일을 직접 실행했을 때만 서버를 시작한다.
    main()  # 초기화 후 TCP 서버를 실행한다.
