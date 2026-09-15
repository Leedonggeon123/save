from __future__ import annotations  # 타입 힌트를 지연 평가한다.

import hashlib  # 비밀번호 해시 생성에 사용한다.
import secrets  # 예측하기 어려운 salt를 생성한다.
import sqlite3  # SQLite 데이터베이스를 열고 SQL을 실행한다.
from datetime import datetime, timezone  # UTC 기준 생성 시각을 만든다.
from pathlib import Path  # 운영체제와 무관하게 파일 경로를 조합한다.

BASE_DIR = Path(__file__).resolve().parents[1]  # mail_client 프로젝트 경로를 구한다.
DATA_DIR = BASE_DIR / "data"  # DB를 저장할 data 폴더 경로다.
DB_PATH = DATA_DIR / "jewel_cloud.sqlite3"  # 기본 SQLite DB 파일 경로다.


def now() -> str:
    return datetime.now(timezone.utc).isoformat()  # UTC ISO 형식 현재 시각을 반환한다.


def password_hash(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)  # 계정별 고유 salt를 생성한다.
    digest = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=64).hex()  # scrypt로 비밀번호를 해시한다.
    return salt, digest  # 저장할 salt와 해시를 반환한다.


def initialize(path: Path = DB_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)  # DB 상위 폴더가 없으면 생성한다.
    connection = sqlite3.connect(path)  # SQLite 파일을 열거나 새로 만든다.
    connection.execute("PRAGMA foreign_keys=ON")  # 외래키 제약조건을 활성화한다.
    # 여러 테이블 생성 SQL을 실행한다.
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS USER (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 사용자 고유 ID를 자동 생성한다.
        email VARCHAR(255) NOT NULL UNIQUE, -- 로그인 이메일 중복을 금지한다.
        password_hash VARCHAR(255) NOT NULL, -- 평문이 아닌 비밀번호 해시를 저장한다.
        password_salt VARCHAR(255) NOT NULL, -- 해시 생성에 사용한 salt를 저장한다.
        name VARCHAR(50) NOT NULL, -- 화면에 표시할 사용자 이름이다.
        grade VARCHAR(20) NOT NULL DEFAULT '일반', -- 사용자 등급이다.
        file_limit BIGINT NOT NULL DEFAULT 104857600, -- 파일 저장 한도(바이트)다.
        is_admin BOOLEAN NOT NULL DEFAULT 0, -- 관리자 여부다.
        is_banned BOOLEAN NOT NULL DEFAULT 0 -- 로그인 차단 여부다.
    );
    CREATE TABLE IF NOT EXISTS File_Metadata (
        file_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 파일 메타데이터 고유 ID다.
        user_id INTEGER NOT NULL, -- 파일 소유자 ID다.
        file_name VARCHAR(255) NOT NULL, -- 원래 파일명이다.
        file_size BIGINT NOT NULL DEFAULT 0, -- 파일 크기다.
        file_path VARCHAR(500) NOT NULL, -- 서버 저장 경로다.
        FOREIGN KEY(user_id) REFERENCES USER(user_id) ON DELETE CASCADE -- 사용자 삭제 시 파일 정보도 삭제한다.
    );
    CREATE TABLE IF NOT EXISTS USER_SETTINGS (
        setting_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 설정 행 고유 ID다.
        user_id INTEGER NOT NULL UNIQUE, -- 사용자당 설정 행 하나만 허용한다.
        default_sender_email VARCHAR(255), -- 기본 발신 이메일이다.
        prefix_msg VARCHAR(1024), -- 메일 앞 자동 문구다.
        suffix_msg VARCHAR(1024), -- 메일 뒤 자동 문구다.
        download_path VARCHAR(500), -- 파일 다운로드 기본 경로다.
        auto_fit BOOLEAN NOT NULL DEFAULT 1, -- 자동 맞춤 사용 여부다.
        auto_fit_chars INTEGER NOT NULL DEFAULT 0, -- 자동 맞춤 글자 수 제한이다.
        auto_fit_sentence VARCHAR(1024) NOT NULL DEFAULT '', -- 자동 삽입 기본 문장이다.
        trash_retention_days INTEGER NOT NULL DEFAULT 30, -- 휴지통 보관 기간이다.
        FOREIGN KEY(user_id) REFERENCES USER(user_id) ON DELETE CASCADE -- 사용자 삭제 시 설정도 삭제한다.
    );
    CREATE TABLE IF NOT EXISTS MESSAGES (
        msg_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 메일 고유 ID다.
        sender_id INTEGER NOT NULL, -- 발신자 USER ID다.
        receiver_id INTEGER NOT NULL, -- 수신자 USER ID다.
        content VARCHAR(1024) NOT NULL, -- 메일 본문이다.
        is_read BOOLEAN NOT NULL DEFAULT 0, -- 읽음 여부다.
        created_at DATETIME NOT NULL, -- 메일 생성 시각이다.
        subject VARCHAR(255) NOT NULL DEFAULT '(제목 없음)', -- 메일 제목이다.
        folder VARCHAR(20) NOT NULL DEFAULT 'inbox', -- 현재 메일 위치다.
        previous_folder VARCHAR(20) NOT NULL DEFAULT '', -- 복구할 때 사용할 삭제 전 위치다.
        deleted_at DATETIME, -- 휴지통으로 이동한 시각이다.
        FOREIGN KEY(sender_id) REFERENCES USER(user_id), -- 발신자 존재 여부를 보장한다.
        FOREIGN KEY(receiver_id) REFERENCES USER(user_id) -- 수신자 존재 여부를 보장한다.
    );
    CREATE TABLE IF NOT EXISTS TEMP_MESSAGES (
        temp_msg_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 임시 메일 고유 ID다.
        sender_id INTEGER NOT NULL, -- 작성자 USER ID다.
        receiver_id INTEGER, -- 단일 수신자 ID를 저장할 수 있다.
        recipient_emails VARCHAR(2048) NOT NULL DEFAULT '', -- 여러 수신자 이메일을 저장한다.
        content VARCHAR(1024) NOT NULL, -- 임시 본문이다.
        subject VARCHAR(255) NOT NULL DEFAULT '(제목 없음)', -- 임시 제목이다.
        created_at DATETIME NOT NULL, -- 임시 저장 시각이다.
        FOREIGN KEY(sender_id) REFERENCES USER(user_id), -- 작성자 존재 여부를 보장한다.
        FOREIGN KEY(receiver_id) REFERENCES USER(user_id) -- 수신자 존재 여부를 보장한다.
    );
    CREATE TABLE IF NOT EXISTS BLACKLIST (
        blocker_id INTEGER NOT NULL, -- 차단 설정자 ID다.
        blocked_id INTEGER NOT NULL, -- 차단 대상 ID다.
        PRIMARY KEY(blocker_id, blocked_id), -- 같은 차단 관계의 중복을 막는다.
        FOREIGN KEY(blocker_id) REFERENCES USER(user_id) ON DELETE CASCADE, -- 설정자 삭제 시 관계도 삭제한다.
        FOREIGN KEY(blocked_id) REFERENCES USER(user_id) ON DELETE CASCADE -- 대상 삭제 시 관계도 삭제한다.
    );
    """)
    # 기존 DB에도 새 기능에 필요한 컬럼을 추가해 기존 데이터를 유지한다.
    setting_columns = {row[1] for row in connection.execute("PRAGMA table_info(USER_SETTINGS)").fetchall()}  # 설정 컬럼 목록을 읽는다.
    if "auto_fit_chars" not in setting_columns:  # 자동 맞춤 글자 수 컬럼이 없으면 추가한다.
        connection.execute("ALTER TABLE USER_SETTINGS ADD COLUMN auto_fit_chars INTEGER NOT NULL DEFAULT 0")
    if "auto_fit_sentence" not in setting_columns:  # 자동 맞춤 문장 컬럼이 없으면 추가한다.
        connection.execute("ALTER TABLE USER_SETTINGS ADD COLUMN auto_fit_sentence VARCHAR(1024) NOT NULL DEFAULT ''")
    if "trash_retention_days" not in setting_columns:  # 휴지통 보관 기간 컬럼이 없으면 추가한다.
        connection.execute("ALTER TABLE USER_SETTINGS ADD COLUMN trash_retention_days INTEGER NOT NULL DEFAULT 30")
    temp_columns = {row[1] for row in connection.execute("PRAGMA table_info(TEMP_MESSAGES)").fetchall()}  # 임시 메일 컬럼 목록을 읽는다.
    if "recipient_emails" not in temp_columns:  # 여러 수신자 저장 컬럼이 없으면 추가한다.
        connection.execute("ALTER TABLE TEMP_MESSAGES ADD COLUMN recipient_emails VARCHAR(2048) NOT NULL DEFAULT ''")
    message_columns = {row[1] for row in connection.execute("PRAGMA table_info(MESSAGES)").fetchall()}  # 메일 컬럼 목록을 읽는다.
    if "previous_folder" not in message_columns:  # 삭제 전 위치 컬럼이 없으면 추가한다.
        connection.execute("ALTER TABLE MESSAGES ADD COLUMN previous_folder VARCHAR(20) NOT NULL DEFAULT ''")
    if "deleted_at" not in message_columns:  # 휴지통 이동 시각 컬럼이 없으면 추가한다.
        connection.execute("ALTER TABLE MESSAGES ADD COLUMN deleted_at DATETIME")
    existing = connection.execute("SELECT COUNT(*) FROM USER").fetchone()[0]  # 기존 사용자 수를 확인한다.
    if not existing:  # 새 DB일 때만 기본 계정을 생성한다.
        for email, password, name, admin, grade, limit_bytes in (
            ("admin@jewel.cloud", "admin1234", "Jewel 관리자", 1, "관리자", 1073741824),
            ("user@jewel.cloud", "user1234", "데모 사용자", 0, "일반", 104857600),
        ):
            salt, digest = password_hash(password)  # 기본 계정 비밀번호를 해시한다.
            cur = connection.execute("INSERT INTO USER(email,password_hash,password_salt,name,grade,file_limit,is_admin) VALUES(?,?,?,?,?,?,?)", (email, digest, salt, name, grade, limit_bytes, admin))  # 사용자 정보를 저장한다.
            connection.execute("INSERT INTO USER_SETTINGS(user_id,default_sender_email) VALUES(?,?)", (cur.lastrowid, email))  # 사용자별 기본 설정도 생성한다.
    connection.commit()  # 모든 스키마와 기본 데이터 변경을 확정한다.
    connection.close()  # DB 연결과 잠금을 해제한다.
    return path  # 초기화한 DB 경로를 반환한다.


if __name__ == "__main__":  # 이 파일을 직접 실행할 때만 초기화를 시작한다.
    print(f"Initialized database: {initialize()}")  # 초기화 완료 메시지와 경로를 출력한다.
