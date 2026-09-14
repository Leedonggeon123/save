"""회원가입 클라이언트 API. PySide6 가입 화면의 버튼 핸들러에서 호출하세요."""
from __future__ import annotations
import requests

SERVER_URL = "http://127.0.0.1:8000"

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
