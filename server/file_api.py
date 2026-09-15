# file_api.py는 클라이언트 요청 접수

"""
주요 API:
- POST /files/upload
  파일을 서버에 업로드

- GET /files
  사용자의 파일 목록 조회

- GET /files/download
  서버 파일 다운로드

- DELETE /files
  서버 파일 삭제

처리 흐름:
클라이언트 요청
→ FastAPI API 수신
→ file_service.py 함수 실행
→ 처리 결과를 JSON 또는 파일로 응답
"""





from .auth_db import db                                                                 # db연결
from pathlib import Path                                                            # 파일 경로를 다루는 도구 
import shutil                                                                        # 파일을 복사하는 도구 
from pydantic import BaseModel

from fastapi import APIRouter, File, HTTPException, UploadFile                       # FastAPI에서 필요한 기능을 가져오기

from fastapi.responses import FileResponse

from .file_service import (                                                         # .으로 상대 경로 사용 
    get_unique_path,
    list_files,
    delete_file as remove_file,
)


router = APIRouter(                                                                 # 파일 전용 API 창구를 만드는 코드
    prefix="/files",                                                                # files 주소 만들어짐
    tags=["files"],
)



@router.get("/settings/{user_id}")                                              # 
def get_file_settings(user_id: int):
    # user_id로 DB에서 등급과 파일 제한값 조회
    with db() as cursor:
        cursor.execute(
            """
            SELECT grade, file_limit
            FROM `USER`
            WHERE user_id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="사용자를 찾을 수 없습니다."
        )

    return {
        "grade": user["grade"],
        "file_limit": user["file_limit"]
    }

@router.post("/upload")                                                             # POST/files/upload 주소를 만듬 
async def upload_file(                                                              # 서버가 받을 값을 정하는 부분                                                                     
    user_id: int,                                                                   # 파일을 올린 사용자 번호
    upload_file: UploadFile = File(...),                                            # 실제 업로드한 파일
):
    user_folder = Path("storage") / str(user_id)                                    # 사용자별 폴더 경로를 만드는 코드   (사용자 번호가 1이라면 storage/1 이라는 경로 생성)
    user_folder.mkdir(parents=True, exist_ok=True)                                  # storage/1 폴더가 없으면 새로 만들기 

    if upload_file.filename is None:
        raise HTTPException(
            status_code=400,
            detail="파일 이름이 없습니다.",
        )

    save_path = get_unique_path(                                                    # 지정할 파일 경로 정하기
        user_folder,                                                                 # 같은 이름이 이미 있으면 _1 처럼 바꿔짐
        upload_file.filename,
    )

    try:                                                                            # 파일 실제 저장 부분 
        with save_path.open("wb") as file:                                          # save_path 저장할 위치                       
            shutil.copyfileobj(upload_file.file, file)                              # copyfileobj 업로드된 파일을 저장위치로 복사 (upload_file.file 업로드된 파일)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"파일 저장 실패: {error}",
        )

    return {                                                                            # 파일을 저장한뒤 결과를 json으로 보냄                                            
        "message": "파일 업로드 완료",                                                   # 성공메세지
        "file_name": save_path.name,                                                    # 저장된 파일 이름
        "file_size": save_path.stat().st_size,                                          # 파일 크기
        "file_path": str(save_path),                                                    # 저장된 위치        
    }
    
@router.get("")
def get_file_list(user_id: int):
    """
    특정 사용자의 파일 목록을 반환한다.
    """
    return {
        "files": list_files(user_id)
    }


@router.get("/download", response_class=FileResponse)           # response_class=FileResponse (다운로드 응답이 파일형식으로 처리된다는 것을 Fast api에게 알려줌)
def download_file(file_path: str):
    path = Path(file_path)

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="파일을 찾을 수 없습니다.",
        )

    return FileResponse(
        path=path,
        filename=path.name,
        media_type="application/octet-stream",
    )
    
    
    
@router.delete("")
def delete_server_file(file_path: str):
    """
    서버에 저장된 파일을 삭제한다.
    """
    try:
        remove_file(file_path)

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="파일을 찾을 수 없습니다.",
        )

    return {
        "message": "파일 삭제 완료",
        "file_path": file_path,
    }
    
    

@router.put("/settings/file-limit")
def update_file_limit(user_id: int, file_limit: int):
    """
    파일 설정에서 입력한 제한값을 USER.file_limit에 저장합니다.
    file_limit은 Byte 단위입니다.
    0이면 등급 기본 제한을 사용합니다.
    """

    # 음수 제한값 방지
    if file_limit < 0:
        raise HTTPException(
            status_code=400,
            detail="파일 제한값은 0 이상이어야 합니다."
        )

    with db() as cursor:
        # 사용자 존재 여부 확인
        cursor.execute(
            """
            SELECT user_id
            FROM `USER`
            WHERE user_id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="사용자를 찾을 수 없습니다."
            )

        # USER 테이블의 파일 제한값 수정
        cursor.execute(
            """
            UPDATE `USER`
            SET file_limit = %s
            WHERE user_id = %s
            """,
            (file_limit, user_id)
        )

    return {
        "saved": True,
        "user_id": user_id,
        "file_limit": file_limit
    }