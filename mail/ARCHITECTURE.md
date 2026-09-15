# Jewel Cloud 서버-클라이언트 구조

```text
Browser Client (public/index.html, app.js, app.css)
        │ HTTP/JSON + multipart over TCP/IP
        ▼
FastAPI (main.py)
  ├─ 인증/세션/권한
  ├─ 파일 API ───────── data/files/
  ├─ 메일/임시메일 API
  ├─ 개인설정/블랙리스트 API
  └─ 관리자 공지/등급/차단 API
        │ SQL + foreign keys
        ▼
SQLite (data/jewel_cloud.sqlite3)
  USER 1:N File_Metadata
  USER 1:N USER_SETTINGS
  USER 1:N MESSAGES / TEMP_MESSAGES
  USER N:N USER via BLACKLIST
```

## 데이터 정의서 매핑

| 정의서 테이블 | 구현 테이블 | 주요 기능 |
|---|---|---|
| USER | `USER` | 회원가입, 로그인, 등급, 관리자/차단 상태 |
| File_Metadata | `File_Metadata` | 업로드, 다운로드, 삭제, 파일 목록 |
| USER_SETTINGS | `USER_SETTINGS` | 기본 발신자, 접두/접미 문구, 다운로드 위치, 자동맞춤 |
| MESSAGES | `MESSAGES` | 받은메일, 보낸메일, 메일 상세, 읽음 상태 |
| TEMP_MESSAGES | `TEMP_MESSAGES` | 임시 보관함 |
| BLACKLIST | `BLACKLIST` | 사용자별 블랙리스트 추가/해제 |

FastAPI의 `/docs`에서 전체 API 계약을 확인할 수 있습니다. 운영 환경에서는 세션 저장소를 Redis로 분리하고 SQLite를 PostgreSQL, `data/files`를 S3 호환 오브젝트 스토리지로 교체하면 됩니다.
