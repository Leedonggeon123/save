"""회원가입·이메일 인증·로그인을 처리하는 서버 코드.

화면(sign.py)이 이 파일의 API 주소를 호출하고, 이 파일이 MariaDB와 Gmail SMTP를 사용합니다.
비밀번호와 인증번호는 평문으로 DB에 저장하지 않습니다.
"""
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

class SenderEmailUpdate(BaseModel):
    user_id: int
    default_sender_email: EmailStr

class ProfileUpdate(BaseModel):
    user_id: int
    name: str = Field(min_length=1, max_length=50)
    password: str | None = Field(default=None, min_length=10, max_length=128)

class CodeCheckRequest(BaseModel):
    email: EmailStr
    verification_code: str = Field(min_length=6, max_length=6, pattern=r"^[0-9]{6}$")

def validate_gmail(email: str) -> None:
    # Requirements specify Google mail; use this restriction until provider policy changes.
    if not email.lower().endswith(("@gmail.com", "@googlemail.com")):
        raise HTTPException(422, "Google Gmail 주소만 사용할 수 있습니다.")

def validate_password(password: str) -> None:
    """영문과 숫자를 포함한 ASCII 10자 이상 비밀번호인지 검사합니다."""
    if len(password) < 10 or not all("!" <= ch <= "~" for ch in password):
        raise HTTPException(422, "비밀번호는 영문·숫자·특수문자로 10자 이상 입력하세요.")
    if not any(ch.isascii() and ch.isalpha() for ch in password) or not any(ch.isdigit() for ch in password):
        raise HTTPException(422, "비밀번호에는 영문과 숫자를 각각 하나 이상 포함하세요.")

def send_gmail_code(email: str, code: str) -> None:
    """서버의 Gmail 발송 계정으로 인증 메일을 보냅니다."""
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
    """서버 시작 시 인증번호 저장 테이블을 준비합니다."""
    ensure_auth_table()

@router.post("/signup/request-code", status_code=202)
def request_code(request: EmailRequest):
    """이메일별로 새 인증번호를 저장하고 Gmail로 발송합니다."""
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
    """인증번호가 일치할 때만 USER 테이블에 회원을 추가합니다."""
    validate_gmail(str(request.email))
    if request.password:
        validate_password(request.password)
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
        # 가입 직후에는 로그인 이메일을 기본 발신 이메일로 저장합니다.
        c.execute("INSERT INTO USER_SETTINGS(user_id,default_sender_email) VALUES(%s,%s)", (user_id, email))
        c.execute("DELETE FROM email_verification WHERE email=%s", (email,))
    return {"user_id": user_id, "message": "회원가입이 완료되었습니다."}

@router.post("/signup/check-email")
def check_email(request: EmailRequest):
    """회원가입 전에 USER.email 중복 여부를 확인합니다."""
    validate_gmail(str(request.email))
    with db() as c:
        c.execute("SELECT 1 FROM `USER` WHERE email=%s", (str(request.email),))
        if c.fetchone(): raise HTTPException(409, "이미 가입된 이메일입니다.")
    return {"available": True, "message": "사용 가능한 이메일입니다."}

@router.post("/signup/verify-code")
def verify_code(request: CodeCheckRequest):
    """화면의 인증번호 확인 버튼이 호출하는 API입니다. 코드는 가입 완료 전까지 보존합니다."""
    email = str(request.email)
    with db() as c:
        c.execute("SELECT * FROM email_verification WHERE email=%s FOR UPDATE", (email,)); row = c.fetchone()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if not row or row["expires_at"] < now: raise HTTPException(400, "인증 코드가 없거나 만료되었습니다.")
        if row["attempts"] >= 5 or not verify_password(request.verification_code, row["code_hash"]):
            c.execute("UPDATE email_verification SET attempts=attempts+1 WHERE email=%s", (email,))
            raise HTTPException(400, "인증 코드가 올바르지 않습니다.")
    return {"verified": True, "message": "인증번호가 일치합니다."}

@router.post("/login")
def login(request: LoginRequest):
    """이메일과 해시 비밀번호를 비교해 로그인합니다."""
    with db() as c:
        c.execute("SELECT user_id,email,password_hash,name,is_banned FROM `USER` WHERE email=%s", (str(request.email),)); user = c.fetchone()
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(401, "이메일 또는 비밀번호가 올바르지 않습니다.")
    if user["is_banned"]: raise HTTPException(403, "정지된 계정입니다.")
    # Temporary compatibility token. Replace with the project's shared JWT/session service when ready.
    token = secrets.token_urlsafe(32)
    return {"token": token, "access_token": token, "user_id": user["user_id"], "name": user["name"]}

@router.put("/settings/default-sender-email")
def update_default_sender_email(request: SenderEmailUpdate):
    """기본 이메일 입력이 끝나는 즉시 USER_SETTINGS에 저장합니다."""
    email = str(request.default_sender_email)
    with db() as c:
        c.execute("SELECT user_id FROM `USER` WHERE user_id=%s", (request.user_id,))
        if not c.fetchone():
            raise HTTPException(404, "사용자를 찾을 수 없습니다.")
        c.execute("SELECT setting_id FROM USER_SETTINGS WHERE user_id=%s LIMIT 1", (request.user_id,))
        row = c.fetchone()
        if row:
            c.execute("UPDATE USER_SETTINGS SET default_sender_email=%s WHERE setting_id=%s", (email, row["setting_id"]))
        else:
            c.execute("INSERT INTO USER_SETTINGS(user_id,default_sender_email) VALUES(%s,%s)", (request.user_id, email))
    return {"saved": True, "default_sender_email": email}

@router.get("/settings/default-sender-email/{user_id}")
def get_default_sender_email(user_id: int):
    """개인설정 화면에 현재 기본 이메일을 보여줍니다."""
    with db() as c:
        c.execute("SELECT default_sender_email FROM USER_SETTINGS WHERE user_id=%s LIMIT 1", (user_id,))
        row = c.fetchone()
    return {"default_sender_email": row["default_sender_email"] if row else ""}

@router.put("/settings/profile")
def update_profile(request: ProfileUpdate):
    """개인정보 화면에서 이름과 비밀번호를 수정합니다."""
    if request.password:
        validate_password(request.password)
    with db() as c:
        c.execute("SELECT user_id FROM `USER` WHERE user_id=%s", (request.user_id,))
        if not c.fetchone():
            raise HTTPException(404, "사용자를 찾을 수 없습니다.")
        if request.password:
            c.execute(
                "UPDATE `USER` SET name=%s, password_hash=%s WHERE user_id=%s",
                (request.name, hash_password(request.password), request.user_id),
            )
        else:
            c.execute("UPDATE `USER` SET name=%s WHERE user_id=%s", (request.name, request.user_id))
    return {"saved": True, "message": "개인정보가 수정되었습니다."}
