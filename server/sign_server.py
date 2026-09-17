# 현재 server.main에 등록되지 않은 이전 회원가입 서버 코드입니다. 현재 회원가입 API는 server/auth_api.py에서 제공합니다.
"""회원가입 클라이언트 API. PySide6 가입 화면의 버튼 핸들러에서 호출하세요."""
from __future__ import annotations
import os
import requests

SERVER_URL = os.getenv("JEWEL_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")

def request_verification_code(email: str) -> dict:
    response = requests.post(f"{SERVER_URL}/api/signup/request-code", json={"email": email}, timeout=15)
    response.raise_for_status()
    return response.json()

def signup(email: str, name: str, password: str, verification_code: str) -> dict:
    response = requests.post(f"{SERVER_URL}/api/signup", json={
        "email": email, "name": name, "password": password,
        "verification_code": verification_code,
    }, timeout=15)
    response.raise_for_status()
    return response.json()
