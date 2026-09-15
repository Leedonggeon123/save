from fastapi import FastAPI
from .file_api import router as file_router
from .auth_api import router as auth_router

from .file_api import router                            # .으로 상대경로 사용


app = FastAPI(                                          # fastapi 서버 객체 생성
    title="JewelCloud Server",
)


app.include_router(router)                                  # 파일 관련 api를 전체 서버에 등록

app.include_router(auth_router)