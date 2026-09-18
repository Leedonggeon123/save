"""PySide6 메일 클라이언트가 사용하는 JSON-over-TCP 프레임 프로토콜.

TCP is a byte stream, so every frame is:

    [4바이트 big-endian JSON 헤더 길이][JSON 헤더][선택적 payload]

The JSON header may contain ``payload_size``. Mail requests normally have no
binary payload; the same framing can later carry file chunks.
"""
from __future__ import annotations  # 타입 힌트를 지연 평가한다.

import json  # Python 객체와 JSON 문자열 사이를 변환한다.
import socket  # TCP 소켓 타입과 recv/send 동작에 사용한다.
import struct  # 헤더 길이를 고정된 4바이트 정수로 변환한다.
from typing import Any  # 요청 데이터의 다양한 타입을 표현한다.

HEADER = struct.Struct("!I")  # !는 네트워크 바이트 순서, I는 4바이트 unsigned int를 의미한다.
MAX_HEADER = 1024 * 1024  # JSON 헤더가 1MiB를 넘지 않도록 제한한다.
MAX_PAYLOAD = 64 * 1024 * 1024  # 첨부파일 등 payload의 최대 크기를 64MiB로 제한한다.


class ProtocolError(Exception):
    """프레임 형식이 잘못되거나 크기 제한을 초과했을 때 발생시키는 예외."""


def _read_exact(sock: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []  # 여러 번 나뉘어 도착할 수 있는 데이터를 임시로 모은다.
    remaining = size  # 아직 받아야 하는 바이트 수를 추적한다.
    while remaining:  # 필요한 바이트를 모두 받을 때까지 반복한다.
        chunk = sock.recv(remaining)  # TCP 스트림에서 남은 크기만큼 읽는다.
        if not chunk:  # 빈 bytes는 상대방이 연결을 닫았다는 의미다.
            raise ConnectionError("TCP peer closed the connection")  # 상위 재연결 로직이 처리하도록 예외를 전달한다.
        chunks.append(chunk)  # 이번에 받은 조각을 저장한다.
        remaining -= len(chunk)  # 남은 수신 바이트 수를 줄인다.
    return b"".join(chunks)  # 조각들을 합쳐 정확한 크기의 완성 데이터를 반환한다.


def send_frame(sock: socket.socket, message: dict[str, Any], payload: bytes = b"") -> None:
    header = dict(message)  # 호출자가 준 메시지를 복사해 원본을 변경하지 않는다.
    if payload:  # 바이너리 데이터가 있을 때만 payload 길이를 헤더에 기록한다.
        header["payload_size"] = len(payload)  # 수신자가 뒤에서 읽을 payload 크기를 알 수 있게 한다.
    encoded = json.dumps(header, ensure_ascii=False, separators=(",", ":")).encode("utf-8")  # JSON을 UTF-8 바이트로 인코딩한다.
    if len(encoded) > MAX_HEADER:  # 비정상적으로 큰 JSON 헤더를 차단한다.
        raise ProtocolError("JSON header is too large")  # 메모리 과다 사용을 방지한다.
    if len(payload) > MAX_PAYLOAD:  # payload가 허용된 최대 크기를 넘는지 검사한다.
        raise ProtocolError("payload is too large")  # 대용량 데이터 공격과 오류를 예방한다.
    sock.sendall(HEADER.pack(len(encoded)) + encoded + payload)  # 길이 헤더, JSON, payload를 순서대로 한 번에 보낸다.


def recv_frame(sock: socket.socket) -> tuple[dict[str, Any], bytes]:
    (header_size,) = HEADER.unpack(_read_exact(sock, HEADER.size))  # 먼저 4바이트 헤더 길이를 읽는다.
    if header_size <= 0 or header_size > MAX_HEADER:  # 헤더 길이가 유효 범위인지 검사한다.
        raise ProtocolError("invalid JSON header length")  # 잘못된 길이로 인한 비정상 수신을 막는다.
    header = json.loads(_read_exact(sock, header_size).decode("utf-8"))  # 지정된 길이만큼 JSON 헤더를 읽고 Python 객체로 변환한다.
    if not isinstance(header, dict):  # 프로토콜 헤더는 반드시 객체여야 한다.
        raise ProtocolError("JSON header must be an object")  # 배열·문자열 등 잘못된 형식을 차단한다.
    payload_size = int(header.pop("payload_size", 0) or 0)  # 헤더에서 payload 길이를 꺼내고 없으면 0으로 처리한다.
    if payload_size < 0 or payload_size > MAX_PAYLOAD:  # 음수 또는 최대 크기 초과를 검사한다.
        raise ProtocolError("invalid payload length")  # 잘못된 payload 요청을 차단한다.
    payload = _read_exact(sock, payload_size) if payload_size else b""  # payload가 있으면 정확한 크기만큼 읽는다.
    return header, payload  # payload_size를 제외한 헤더와 실제 payload를 반환한다.


def request_message(message_type: str, request_id: str, **data: Any) -> dict[str, Any]:
    """메일 화면에서 공통으로 사용하는 요청 봉투를 생성한다."""
    return {
        "type": message_type,  # LOGIN_REQUEST, LIST_MAILS 등 서버가 실행할 작업 종류다.
        "request_id": request_id,  # 응답과 원래 요청을 연결하는 고유 ID다.
        "session_id": data.pop("session_id", None),  # 로그인 후 인증 상태를 식별한다.
        "data": data,  # 작업별 인자를 data 객체 안에 넣는다.
    }
