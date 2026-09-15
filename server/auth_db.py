"""인증 API가 MariaDB를 사용하도록 돕는 DB 유틸리티 모듈입니다."""
from __future__ import annotations
import hashlib  # 비밀번호 해시 계산에 사용합니다.
import hmac  # 해시 비교를 안전하게 수행합니다.
import os  # .env에서 DB 접속 설정을 읽습니다.
import secrets  # 랜덤 salt를 생성합니다.
from contextlib import contextmanager  # commit/rollback을 자동화합니다.
from pathlib import Path
from typing import Iterator
import pymysql  # MariaDB 접속 드라이버입니다.
from dotenv import load_dotenv  # .env 로더입니다.

# 프로젝트 루트의 .env에서 DB 접속 설정을 읽습니다.
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)


def connect():
    """환경변수로 MariaDB 연결을 생성합니다."""
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),  # DB 서버 주소입니다.
        port=int(os.getenv("DB_PORT", "3306")),  # MariaDB 포트입니다.
        user=os.environ["DB_USER"],  # DB 계정입니다.
        password=os.environ["DB_PASSWORD"],  # DB 비밀번호입니다.
        database=os.getenv("DB_NAME", "jewel_cloud"),  # 사용할 DB입니다.
        charset="utf8mb4",  # 한글 저장용 문자셋입니다.
        cursorclass=pymysql.cursors.DictCursor,  # 조회 결과를 dict로 받습니다.
        autocommit=False,  # 작업 완료 후 직접 commit합니다.
        connect_timeout=5,  # 연결 대기 시간을 제한합니다.
    )


@contextmanager
def db() -> Iterator[pymysql.cursors.DictCursor]:
    """SQL 성공 시 commit하고 오류 시 rollback하는 DB 작업 관리자입니다."""
    connection = connect()  # 요청마다 DB 연결을 생성합니다.
    try:
        with connection.cursor() as cursor:  # SQL 실행용 cursor를 엽니다.
            yield cursor  # auth_api.py가 이 cursor를 사용합니다.
        connection.commit()  # 모든 SQL이 성공하면 변경을 확정합니다.
    except Exception:
        connection.rollback()  # 하나라도 실패하면 변경을 취소합니다.
        raise  # 원래 오류를 API 계층으로 전달합니다.
    finally:
        connection.close()  # 연결을 닫아 DB 자원을 반환합니다.


def ensure_auth_table() -> None:
    """서버 시작 시 인증번호 임시 저장 테이블을 생성합니다."""
    with db() as cursor:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS email_verification (
              email VARCHAR(255) NOT NULL PRIMARY KEY,
              code_hash VARCHAR(255) NOT NULL,
              expires_at DATETIME NOT NULL,
              attempts TINYINT UNSIGNED NOT NULL DEFAULT 0,
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB"""
        )


def hash_password(password: str) -> str:
    """비밀번호 또는 인증번호를 PBKDF2-SHA256으로 해시합니다."""
    salt = secrets.token_bytes(16)  # 매번 다른 salt를 생성합니다.
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return "pbkdf2_sha256$310000$" + salt.hex() + "$" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    """입력값을 저장된 해시와 비교해 일치 여부를 반환합니다."""
    try:
        algorithm, rounds, salt, digest = stored.split("$")  # 저장값을 분리합니다.
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), int(rounds)
        )  # 저장된 salt와 반복 횟수로 재계산합니다.
        return algorithm == "pbkdf2_sha256" and hmac.compare_digest(
            candidate.hex(), digest
        )  # 계산 결과와 저장된 해시를 안전하게 비교합니다.
    except (ValueError, TypeError):
        return False  # 해시 형식이 잘못되면 인증 실패입니다.
