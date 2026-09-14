from fastapi import FastAPI
from .file_api import router as file_router
from .auth_api import router as auth_router

app = FastAPI(title="JewelCloud Server")
app.include_router(file_router)
app.include_router(auth_router)
