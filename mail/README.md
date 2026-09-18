# Jewel Cloud

요구사항 분석서/순서도/목업과 데이터 정의서의 `USER`, `File_Metadata`, `USER_SETTINGS`, `MESSAGES`, `TEMP_MESSAGES`, `BLACKLIST` 구조를 반영한 FastAPI 기반 웹 클라우드 시스템입니다.

## 실행

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 3000
```

브라우저에서 http://localhost:3000 을 엽니다.

- 기본 관리자: `admin@jewel.cloud` / `admin1234`
- 기본 일반 사용자: `user@jewel.cloud` / `user1234`

데이터는 `data/db.json`, 업로드 파일은 `data/files/`에 저장됩니다. 운영 배포 시 JSON 저장소를 PostgreSQL/S3로 교체하고 세션 저장소를 Redis로 분리하면 됩니다.

## 구조

- `main.py`: FastAPI 인증·권한·파일·메일·관리자 API와 정적 파일 서버
- `server.js`: 의존성 없는 Node 실행용 레거시 프로토타입 (`npm run start:node`)
- `public/index.html`: 목업 흐름을 반영한 단일 클라이언트 앱
- `data/jewel_cloud.sqlite3`: 데이터 정의서에 맞춘 관계형 데이터베이스

## 구현된 흐름

회원가입 → 로그인 → 기본 메뉴 → 파일 업로드/다운로드/삭제 → 메일 작성/임시저장/발송 → 개인설정 → 관리자 공지/차단/등급 관리.

## 서버-클라이언트 관계

브라우저 클라이언트는 TCP/IP 위 HTTP 요청으로 FastAPI REST API에 연결됩니다. FastAPI는 인증/권한을 확인한 뒤 SQLite의 관계형 테이블과 `data/files/` 저장소를 갱신하고 JSON 응답을 반환합니다. API 문서는 서버 실행 후 http://localhost:3000/docs 에서 확인할 수 있습니다.
