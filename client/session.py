from dataclasses import dataclass
from typing import Any

# 생성자 안 적고 클래스 생성
@dataclass
class UserSession:
    """로그인 상태를 화면 사이에서 공유. 비밀번호는 저장X"""
    user_id: int | None = None
    email: str = ""
    name: str = ""
    grade: str = "일반"
    file_limit: int = 0
    is_admin: bool = False
    access_token: str = ""

    # 함수를 변수처럼 편하게 쓸 수 있음
    @property
    def is_authenticated(self) -> bool:
        return bool(self.access_token)

    # 서버에서 반환 받은 로그인한 사용자 정보 저장
    def update_from_login(self, data: dict[str, Any], email: str = "") -> None:
        self.access_token = str(data.get("token") or data.get("access_token") or "")
        self.user_id = data.get("user_id")
        self.email = str(data.get("email") or email or "")
        self.name = str(data.get("name") or "")
        self.grade = str(data.get("grade") or "일반")
        self.file_limit = int(data.get("file_limit") or 0)
        raw_admin = data.get("is_admin", False)
        self.is_admin = (raw_admin.strip().lower() in {"1", "true", "yes", "y", "on"} if isinstance(raw_admin, str) else bool(raw_admin))

    def clear(self) -> None:
        self.user_id = None
        self.email = ""
        self.name = ""
        self.grade = "일반"
        self.file_limit = 0
        self.is_admin = False
        self.access_token = ""
