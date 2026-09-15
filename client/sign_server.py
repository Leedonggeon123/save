"""회원가입 화면에서 호출하는 FastAPI API 클라이언트입니다."""
from __future__ import annotations  # 타입 힌트 평가를 늦춥니다.

import os  # 환경변수에서 서버 주소를 읽습니다.
from typing import Any  # JSON 응답 타입을 설명합니다.
import requests  # HTTP POST 요청을 보냅니다.

# 로컬 실행 기본 주소이며, 원격 서버에서는 JEWEL_SERVER_URL로 덮어씁니다.
SERVER_URL = os.getenv("JEWEL_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")


class ApiError(requests.HTTPError):
    """서버 오류를 화면에서 사용할 사용자용 메시지로 전달합니다."""

    def __init__(self, message: str):
        super().__init__(message)  # requests 예외의 기본 메시지를 초기화합니다.
        self.user_message = message  # SignupWindow가 표시할 한글 메시지를 저장합니다.


def _post(path: str, data: dict[str, Any]) -> dict[str, Any]:
    """회원가입 관련 endpoint에 POST 요청을 보내고 JSON을 반환합니다."""
    response = requests.post(  # 클라이언트에서 FastAPI 서버로 HTTP 요청을 전송합니다.
        f"{SERVER_URL}{path}",  # 기본 서버 주소와 API 경로를 합칩니다.
        json=data,  # 이메일·이름·인증번호 등을 JSON으로 전달합니다.
        timeout=15,  # 서버가 응답하지 않을 때 무한 대기하지 않습니다.
    )
    if response.ok:  # HTTP 2xx이면 요청이 정상 처리된 것입니다.
        return response.json()  # 서버의 성공 응답을 화면 로직으로 반환합니다.

    # 서버가 오류를 반환하면 사용자에게 보여줄 detail을 추출합니다.
    try:
        detail = response.json().get("detail", "요청을 처리하지 못했습니다.")
        if isinstance(detail, list):  # Pydantic 검증 오류는 목록으로 올 수 있습니다.
            detail = detail[0].get("msg", "입력값을 확인해주세요.")
    except (ValueError, AttributeError, IndexError):
        detail = "서버 요청에 실패했습니다."  # JSON이 아닌 오류 응답에 대한 기본 메시지입니다.

    # FastAPI/Pydantic의 대표적인 영어 오류를 화면용 한글 문구로 바꿉니다.
    english_to_korean = {
        "String should have at least 10 characters": "비밀번호는 10자 이상 입력해주세요.",
        "String should have at least 1 character": "필수 입력값을 입력해주세요.",
        "value is not a valid email address": "올바른 이메일 주소를 입력해주세요.",
    }
    detail = english_to_korean.get(str(detail), str(detail))  # 변환되지 않은 오류는 원문을 사용합니다.
    raise ApiError(detail)  # SignupWindow의 예외 처리로 오류를 전달합니다.


def check_email(email: str) -> dict[str, Any]:
    """USER.email 중복 확인 API를 호출합니다."""
    return _post("/api/signup/check-email", {"email": email})


def request_verification_code(email: str) -> dict[str, Any]:
    """Gmail 인증번호 발송 API를 호출합니다."""
    return _post("/api/signup/request-code", {"email": email})


def verify_code(email: str, code: str) -> dict[str, Any]:
    """입력한 인증번호가 서버에 저장된 코드와 일치하는지 확인합니다."""
    return _post(
        "/api/signup/verify-code",
        {"email": email, "verification_code": code},
    )


def signup(email: str, name: str, password: str, code: str) -> dict[str, Any]:
    """인증된 이메일과 사용자 정보를 최종 회원가입 API로 전송합니다."""
    return _post(
        "/api/signup",
        {
            "email": email,
            "name": name,
            "password": password,
            "verification_code": code,
        },
    )
