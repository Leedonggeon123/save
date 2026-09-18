from fastapi import FastAPI
from .file_api import router as file_router
from .auth_api import router as auth_router


from .file_api import router                            # .으로 상대경로 사용
from .auth_db import ensure_auth_table
from mail.mail_client.database.init_db import initialize
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "mail" / "mail_client" / "data" / "jewel_cloud.sqlite3"
initialize(DB_PATH)
ensure_auth_table()




app = FastAPI(                                          # fastapi 서버 객체 생성
    title="JewelCloud Server",
)


app.include_router(file_router)                                  # 파일 관련 api를 전체 서버에 등록
# FastAPI auth_api.py 안의 API들을 인식
app.include_router(auth_router)
