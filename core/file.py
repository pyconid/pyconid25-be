import os
from typing import Optional
from fastapi import UploadFile
from fastapi.responses import FileResponse

from settings import FILE_STORAGE_PATH, MAX_FILE_SIZE_MB


def is_over_max_file_size(upload_file: UploadFile) -> bool:
    return upload_file.size > (MAX_FILE_SIZE_MB * 1024 * 1024)


async def upload_file(upload_file: UploadFile, path: str) -> str:
    contents = await upload_file.read()
    full_path = f"{FILE_STORAGE_PATH}/{path}"
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb") as f:
        f.write(contents)
    return path


def get_file(
    path: str,
) -> Optional[FileResponse]:
    path = f"{FILE_STORAGE_PATH}/{path}"
    if os.path.exists(path=path):
        return FileResponse(path=path)
    else:
        return None
