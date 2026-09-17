"""이전 회원가입 코드 보관 파일. 현재 회원가입 API는 server/auth_api.py에서 제공합니다."""

# def request_verification_code(email: str) -> dict:
#     response = requests.post(f"{SERVER_URL}/api/signup/request-code", json={"email": email}, timeout=15)
#     response.raise_for_status()
#     return response.json()

# def signup(email: str, name: str, password: str, verification_code: str) -> dict:
#     response = requests.post(f"{SERVER_URL}/api/signup", json={
#         "email": email, "name": name, "password": password,
#         "verification_code": verification_code,
#     }, timeout=15)
#     response.raise_for_status()
#     return response.json()
