# file_service.py는 실제로 파일 저장, 조회, 다운로드, 삭제
"""
주요 기능:
1. 파일 업로드 및 서버 폴더 저장
2. 중복 파일명 자동 변경
3. 사용자별 파일 목록 조회
4. 파일 다운로드
5. 파일 삭제
6. 파일 용량 제한 확인
"""

from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORAGE = str(PROJECT_ROOT / "storage")



def get_unique_path(folder: Path, filename: str) -> Path:                               # 이 함수는 저장할 파일의 최종 경로를 정하는 함수 인자(folder는 파일을 저장할 폴더 filename은 저장한 파일 이름) (반환값 중복되지 않는 최종 파일 경로)
    original_path = folder / filename                                       # 폴더와 파일 이름을 합쳐서 원래 저장 경로를 만듬

    if not original_path.exists():                                              # 같은 이름의 파일이 없으면  원래 경로를 그대로 사용
        return original_path

    stem = original_path.stem                                               # 파일 이름과 확장자를 분리 예(photo.png라면 stem은 photo, suffix는 .png)
    suffix = original_path.suffix
    number = 1                                                              # 중복 파일 뒤에 붙일 숫자

    while True:                                                                     # 사용할 수 있는 파일 이름이 나올 때까지 반복
        new_path = folder / f"{stem}_{number}{suffix}"

        if not new_path.exists():                                                   # 새로운 이름의 파일이 없으면 그 경로를 사용
            return new_path

        number += 1                                                                     # 이미 있으면 숫자를 1증가 


def save_file(source_path: str, user_id: int, storage_root: str = DEFAULT_STORAGE) -> dict:
    source = Path(source_path)                                                                  # 사용자가 선택한 원본 파일 경로를 path 객체로 변환

    if not source.exists():                                                                         # 원본 파일이 실제로 있는지 확인
        raise FileNotFoundError("업로드할 파일이 존재하지 않습니다.")                                   

    user_folder = Path(storage_root) / str(user_id)                                         # 사용자별 저장 폴더를 만듬
    user_folder.mkdir(parents=True, exist_ok=True)                                          # 폴더가 없으면 새로 만듬

    save_path = get_unique_path(user_folder, source.name)                               # 중복되지 않는 파일 저장 경로를 만듬
    shutil.copy2(source, save_path)                                                     # 원본 파일을 서버 저장 폴더로 복사

    return {                                                                        # 나중에 db에 저장할 파일 정보를 반환한다.
        "user_id": user_id,                                                             
        "file_name": save_path.name,
        "file_size": save_path.stat().st_size,
        "file_path": str(save_path),
    }


<<<<<<< HEAD
def list_files(user_id: int, storage_root: str = DEFAULT_STORAGE) -> list:
                                                                                # 인자 user_id는 파일 목록을 확인할 사용자 번호
                                                                             # 인자 storage_root는 파일이 저장된 기본 폴더
=======
>>>>>>> origin/main




def list_files(user_id: int, storage_root: str = "storage") -> list:                        # 이 함수는 특정 사용자의 파일과 폴더 목록을 가져오는 함수입니다.
    # user_id는 파일 목록을 확인할 사용자의 번호입니다.
    # storage_root는 파일과 폴더가 저장되어 있는 기본 폴더입니다.

    user_folder = Path(storage_root) / str(user_id)
    # 사용자별 저장 폴더의 경로를 만듭니다.
    # 예: storage/1
    
    if not user_folder.exists():
        # 사용자 폴더가 없으면 파일과 폴더가 없는 것으로 처리합니다.
        return []

    file_list = []
    # 파일과 폴더 정보를 저장할 빈 리스트를 만듭니다.

    for item in user_folder.iterdir():
        # 사용자의 저장 폴더 안에 있는 항목을 하나씩 확인합니다.
        # 여기에는 파일과 폴더가 모두 들어올 수 있습니다.

        if item.is_file():
            # 현재 항목이 실제 파일인지 확인합니다.

            file_list.append({
                "type": "file",
                "file_name": item.name,
                "file_size": item.stat().st_size,
                "file_path": str(item),
            })
            # 파일이라면 파일 정보를 리스트에 추가합니다.
            # type을 file로 저장해서 클라이언트가 파일인지 구분할 수 있게 합니다.

        elif item.is_dir():
            # 현재 항목이 폴더인지 확인합니다.

            file_list.append({
                "type": "folder",
                "file_name": item.name,
                "file_size": 0,
                "file_path": str(item),
            })
            # 폴더라면 폴더 정보를 리스트에 추가합니다.
            # 폴더 자체에는 파일 크기가 없기 때문에 0으로 저장합니다.
            # type을 folder로 저장해서 클라이언트가 폴더인지 구분할 수 있게 합니다.

    return file_list
    # 확인한 파일과 폴더 목록을 반환합니다.





def delete_file(file_path: str) -> None:                                # 이 함수는 서버에 저장된 파일을 삭제하는 함수
                                                                        # 인자 file_path는 삭제할 파일의 서버 경로


    path = Path(file_path)                                                  # 문자열로 받은 파일 경로를 path 객체로 변환

    if not path.exists():                                                       # 파일이 실제로 존재한지 확인 
        raise FileNotFoundError("삭제할 파일이 존재하지 않습니다.")

    path.unlink()                                                                   # 실제 파일 삭제 (이 함수는 api에서 delete를 호출했을 때 사용)


def can_upload(                                                                 # 이 함수는 파일을 업로드 해도 용량 제한을 넘지 않는지 확인하는 함수
    current_usage: int,                                                          # 현재 사용중인 용량 (byte)
    new_file_size: int,                                                         # 새로 업로드할 파일 크기(byte)
    limit_size: int,                                                            # limit_size 사용자가 사용할 수 있는 전체 제한 용량(byte)
) -> bool:
  
    return current_usage + new_file_size <= limit_size                          # 현재 사용량과 새 파일 크기를 합쳐 제한을 넘는지 확인



def download_file(                                              # 이 함수는 서버에 있는 파일을 사용자의 다운로드 폴더로 복사하는 함수
    file_path: str,                                              # 인자 file_path는 서버에 저장된 원본 파일 경로
    destination_folder: str,                                    # 인자 destination_folder는 파일을 내려받을 사용자 폴더 
) -> str:
   
    source = Path(file_path)                                    # 서버 파일 경로를 path 객체로 변환

    if not source.exists():                                                     # 서버에 파일이 실제로 있는지 확인
        raise FileNotFoundError("다운로드할 파일이 존재하지 않습니다.")

    destination = Path(destination_folder)                                      # 다운로드할 폴더를 만듬
    destination.mkdir(parents=True, exist_ok=True)                              # 폴더가 없으면 새로 만듬

    save_path = get_unique_path(destination, source.name)                       # 다운로드 폴더에 같은 이름의 파일이 있는지 확인
    shutil.copy2(source, save_path)                                                 # 서버 파일을 사용자 폴더로 복사

    return str(save_path)                                                           # 실제로 저장된 파일 경로를 반환




def get_storage_usage(user_id: int, storage_root: str = DEFAULT_STORAGE) -> int:
    """
    사용자가 현재 사용 중인 전체 파일 용량을 계산합니다.

    반환값은 Byte 단위입니다.
    예: 1MB 파일 1개 → 1048576
    """

    # 사용자별 저장 폴더 경로를 만듭니다.
    # 예: storage/1
    user_folder = Path(storage_root) / str(user_id)

    # 사용자 폴더가 없으면 사용량은 0Byte입니다.
    if not user_folder.exists():
        return 0

    # 전체 파일 용량을 저장할 변수입니다.
    total_size = 0

    # 사용자 폴더 안의 파일과 하위 폴더를 모두 확인합니다.
    for file_path in user_folder.rglob("*"):

        # 폴더는 제외하고 실제 파일만 계산합니다.
        if file_path.is_file():
            total_size += file_path.stat().st_size

    # 계산된 전체 용량을 Byte 단위로 반환합니다.
    return total_size
<<<<<<< HEAD
=======




def create_folder(user_id: int, folder_name: str, storage_root: str = "storage") -> str:        # 폴더 관리 로직
    # 사용자별 저장 폴더 경로를 만듭니다.
    # 예: storage/1
    user_folder = Path(storage_root) / str(user_id)

    # 사용자의 폴더가 없으면 만듭니다.
    user_folder.mkdir(parents=True, exist_ok=True)

    # 새로 만들 폴더의 경로를 만듭니다.
    folder_path = user_folder / folder_name

    # 폴더를 만듭니다.
    folder_path.mkdir()

    # 만들어진 폴더 경로를 반환합니다.
    return str(folder_path)



def delete_folder(user_id: int, folder_name: str, storage_root: str = "storage") -> None:
    # 사용자별 저장 폴더 경로를 만듭니다.
    # 예: storage/1
    user_folder = Path(storage_root) / str(user_id)

    # 삭제할 폴더의 경로를 만듭니다.
    folder_path = user_folder / folder_name

    # 폴더가 존재하지 않으면 오류를 발생시킵니다.
    if not folder_path.exists():
        raise FileNotFoundError("삭제할 폴더가 존재하지 않습니다.")

    # 폴더 안에 파일이나 다른 폴더가 있으면 삭제하지 않습니다.
    if any(folder_path.iterdir()):                                                      # any(여러 조건 중 하나라도 참인지 확인하는 함수 .iterdir()이 폴더안에 파일이 있는지 검사)
        raise OSError("폴더가 비어있지 않습니다.")                                         # 파일이 있으면 경고 

    # 비어있는 폴더만 삭제합니다.
    folder_path.rmdir()
>>>>>>> origin/main
