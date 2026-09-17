"""회원가입 화면에서 호출하는 FastAPI API 클라이언트"""
from __future__ import annotations  

import os  
from typing import Any  
import requests         # HTTP POST 요청을 보냄

# 로컬 실행 기본 주소, 원격 서버에서는 JEWEL_SERVER_URL로 덮어씀
SERVER_URL = os.getenv("JEWEL_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")


class ApiError(requests.HTTPError):
    """서버 오류를 화면에서 사용할 사용자용 메시지로 전달"""

    def __init__(self, message: str):
        super().__init__(message)  
        self.user_message = message 

def _post(path: str, data: dict[str, Any]) -> dict[str, Any]:
    """회원가입 관련 endpoint에 POST 요청을 보내고 JSON을 반환"""
    # 클라이언트에서 FastAPI 서버로 HTTP 요청을 전송 / 기본 서버 주소와 API 경로를 합침 / 이메일·이름·인증번호 등을 JSON으로 전달
    response = requests.post(f"{SERVER_URL}{path}", json=data, timeout=15)
    # HTTP 2xx이면 요청이 정상 처리
    if response.ok:
        # 서버의 성공 응답을 화면 로직으로 반환
        return response.json() 

    # 서버가 오류를 반환하면 사용자에게 보여줄 에러 창
    try:
        detail = response.json().get("detail", "요청을 처리하지 못했습니다.")
        # Pydantic 검증 오류는 목록으로 옴
        if isinstance(detail, list): 
            detail = detail[0].get("msg", "입력값을 확인해주세요.")
    except (ValueError, AttributeError, IndexError):
        # JSON이 아닌 오류 응답에 대한 기본 메시지
        detail = "서버 요청에 실패했습니다."  

    # 영어 오류를 화면용 한글로 변경
    english_to_korean = {
        "String should have at least 10 characters": "비밀번호는 10자 이상 입력해주세요.",
        "String should have at least 1 character": "필수 입력값을 입력해주세요.",
        "value is not a valid email address": "올바른 이메일 주소를 입력해주세요.",
    }
    detail = english_to_korean.get(str(detail), str(detail))  
    # SignupWindow의 예외 처리로 오류를 전달
    raise ApiError(detail) 


def check_email(email: str) -> dict[str, Any]:
    """USER.email 중복 확인 API를 호출"""
    return _post("/api/signup/check-email", {"email": email})


def request_verification_code(email: str) -> dict[str, Any]:
    """Gmail 인증번호 발송 API를 호출"""
    return _post("/api/signup/request-code", {"email": email})


def verify_code(email: str, code: str) -> dict[str, Any]:
    """입력한 인증번호가 서버에 저장된 코드와 일치하는지 확인"""
    return _post(
        "/api/signup/verify-code",
        {"email": email, "verification_code": code},
    )


def signup(email: str, name: str, phone: str, password: str, code: str) -> dict[str, Any]:
    """인증된 이메일과 사용자 정보를 최종 회원가입 API로 전송"""
    return _post(
        "/api/signup",
        {
            "email": email,
            "name": name,
            "phone": phone,
            "password": password,
            "verification_code": code,
        },
    )
