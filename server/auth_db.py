"""로컬 실행용 SQLite 인증 DB 유틸리티."""
from __future__ import annotations
import hashlib  # 비밀번호 해시 계산에 사용합니다.
import hmac  # 해시 비교를 안전하게 수행합니다.
import os  # .env에서 DB 접속 설정을 읽습니다.
import secrets  # 랜덤 salt를 생성합니다.
import sqlite3
import re
from contextlib import contextmanager  # commit/rollback을 자동화합니다.
from pathlib import Path
from typing import Iterator
from dotenv import load_dotenv  # .env 로더입니다.

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=True)
DB_PATH = Path(os.getenv("CLOUD_DB_PATH", str(PROJECT_ROOT / "mail" / "mail_client" / "data" / "jewel_cloud.sqlite3")))


class SQLiteCursor:
    """기존 MySQL SQL 표기를 로컬 SQLite에서 호환시키는 얇은 어댑터."""
    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    def execute(self, sql, parameters=()):
        sql = sql.replace("%s", "?")
        sql = re.sub(r"\s+FOR UPDATE\b", "", sql, flags=re.IGNORECASE)
        return self._cursor.execute(sql, parameters)

    def __getattr__(self, name):
        return getattr(self._cursor, name)


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


@contextmanager
def db() -> Iterator[SQLiteCursor]:
    connection = connect()
    try:
        cursor = SQLiteCursor(connection.cursor())
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


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
            )"""
        )


def hash_password(password: str) -> str:
    """비밀번호 또는 인증번호를 PBKDF2-SHA256으로 해시합니다."""
    salt = secrets.token_bytes(16)  # 매번 다른 salt를 생성합니다.
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return "pbkdf2_sha256$310000$" + salt.hex() + "$" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    """입력값을 저장된 해시와 비교해 일치 여부를 반환합니다."""
    try:
        parts = stored.split("$")
        if len(parts) == 4 and parts[0] == "pbkdf2_sha256":
            _, rounds, salt, digest = parts
            candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
            return hmac.compare_digest(candidate.hex(), digest)
        if len(parts) == 2:
            salt, digest = parts
            candidate = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=64)
            return hmac.compare_digest(candidate.hex(), digest)
    except (ValueError, TypeError):
        return False  # 해시 형식이 잘못되면 인증 실패입니다.


def ensure_admin_column() -> None:
    """기존 USER 테이블에 관리자 여부 컬럼이 없으면 추가합니다."""
    with db() as cursor:
        cursor.execute(
            """SELECT COUNT(*) AS column_count
               FROM pragma_table_info('USER')
               WHERE name='is_admin'""",
        )
        exists = cursor.fetchone()["column_count"]
        if not exists:
            table_name = chr(96) + "USER" + chr(96)
            cursor.execute(
                "ALTER TABLE " + table_name + " ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0"
            )
