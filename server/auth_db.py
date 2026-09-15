"""MariaDB connection and password helpers used by the auth API."""
from __future__ import annotations
import hashlib, hmac, os, secrets
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
import pymysql
from dotenv import load_dotenv

# Always load the .env beside /home/user/save, even when uvicorn is started
# without first running `source .env` in the shell.
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

def connect():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"), port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
        database=os.getenv("DB_NAME", "jewel_cloud"), charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, autocommit=False, connect_timeout=5,
    )

@contextmanager
def db() -> Iterator[pymysql.cursors.DictCursor]:
    connection = connect()
    try:
        with connection.cursor() as cursor:
            yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def ensure_auth_table() -> None:
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS email_verification (
          email VARCHAR(255) NOT NULL PRIMARY KEY,
          code_hash VARCHAR(255) NOT NULL,
          expires_at DATETIME NOT NULL,
          attempts TINYINT UNSIGNED NOT NULL DEFAULT 0,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB""")

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"pbkdf2_sha256$310000${salt.hex()}${digest.hex()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, rounds, salt, digest = stored.split("$")
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
        return algorithm == "pbkdf2_sha256" and hmac.compare_digest(candidate.hex(), digest)
    except (ValueError, TypeError):
        return False
