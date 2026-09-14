"""회원가입/Google SMTP 인증/로그인 FastAPI router for the existing Jewel server."""
from __future__ import annotations
import os, secrets, smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
import pymysql
from .auth_db import db, ensure_auth_table, hash_password, verify_password

router = APIRouter(prefix="/api", tags=["auth"])
CODE_TTL_MINUTES = 10

class EmailRequest(BaseModel):
    email: EmailStr

class SignupRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=10, max_length=128)
    verification_code: str = Field(min_length=6, max_length=6, pattern=r"^[0-9]{6}$")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def validate_gmail(email: str) -> None:
    # Requirements specify Google mail; use this restriction until provider policy changes.
    if not email.lower().endswith(("@gmail.com", "@googlemail.com")):
        raise HTTPException(422, "Google Gmail 주소만 사용할 수 있습니다.")

def send_gmail_code(email: str, code: str) -> None:
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ.get("SMTP_USER")
    app_password = os.environ.get("SMTP_APP_PASSWORD")
    if not username or not app_password:
        raise HTTPException(500, "SMTP_USER와 SMTP_APP_PASSWORD를 서버 환경 변수에 설정하세요.")
    message = EmailMessage()
    message["Subject"] = "Jewel Cloud 이메일 인증 코드"
    message["From"] = os.environ.get("SMTP_FROM", username)
    message["To"] = email
    message.set_content(f"Jewel Cloud 인증 코드: {code}\n10분 안에 입력하세요.")
    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(username, app_password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise HTTPException(502, "인증 메일 전송에 실패했습니다.") from exc

@router.on_event("startup")
def startup_auth() -> None:
    ensure_auth_table()

@router.post("/signup/request-code", status_code=202)
def request_code(request: EmailRequest):
    validate_gmail(str(request.email))
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=CODE_TTL_MINUTES)
    # email is the primary key: a code always belongs to exactly one address.
    with db() as c:
        c.execute("SELECT user_id FROM `USER` WHERE email=%s", (str(request.email),))
        if c.fetchone():
            raise HTTPException(409, "이미 가입된 이메일입니다.")
        c.execute("""INSERT INTO email_verification(email,code_hash,expires_at,attempts)
                     VALUES(%s,%s,%s,0)
                     ON DUPLICATE KEY UPDATE code_hash=VALUES(code_hash),expires_at=VALUES(expires_at),attempts=0""",
                  (str(request.email), hash_password(code), expires))
    try:
        send_gmail_code(str(request.email), code)
    except HTTPException:
        with db() as c: c.execute("DELETE FROM email_verification WHERE email=%s", (str(request.email),))
        raise
    return {"message": "인증 메일을 전송했습니다."}

@router.post("/signup", status_code=201)
def signup(request: SignupRequest):
    validate_gmail(str(request.email))
    if not any(x.isdigit() for x in request.password) or not any(not x.isalnum() for x in request.password):
        raise HTTPException(422, "비밀번호는 숫자와 특수문자를 포함해 10자 이상이어야 합니다.")
    email = str(request.email)
    with db() as c:
        c.execute("SELECT * FROM email_verification WHERE email=%s FOR UPDATE", (email,)); row = c.fetchone()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if not row or row["expires_at"] < now:
            raise HTTPException(400, "인증 코드가 없거나 만료되었습니다.")
        if row["attempts"] >= 5:
            raise HTTPException(429, "인증 시도 횟수를 초과했습니다. 새 인증 코드를 요청하세요.")
        if not verify_password(request.verification_code, row["code_hash"]):
            c.execute("UPDATE email_verification SET attempts=attempts+1 WHERE email=%s", (email,))
            raise HTTPException(400, "인증 코드가 올바르지 않습니다.")
        try:
            c.execute("INSERT INTO `USER`(email,password_hash,name) VALUES(%s,%s,%s)", (email, hash_password(request.password), request.name))
        except pymysql.IntegrityError as exc:
            raise HTTPException(409, "이미 가입된 이메일입니다.") from exc
        user_id = c.lastrowid
        c.execute("DELETE FROM email_verification WHERE email=%s", (email,))
    return {"user_id": user_id, "message": "회원가입이 완료되었습니다."}

@router.post("/login")
def login(request: LoginRequest):
    with db() as c:
        c.execute("SELECT user_id,email,password_hash,name,is_banned FROM `USER` WHERE email=%s", (str(request.email),)); user = c.fetchone()
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(401, "이메일 또는 비밀번호가 올바르지 않습니다.")
    if user["is_banned"]: raise HTTPException(403, "정지된 계정입니다.")
    # Temporary compatibility token. Replace with the project's shared JWT/session service when ready.
    token = secrets.token_urlsafe(32)
    return {"token": token, "access_token": token, "user_id": user["user_id"], "name": user["name"]}
