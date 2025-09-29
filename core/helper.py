from fastapi import UploadFile
from typing import Optional


def save_file_and_get_url(url: Optional[UploadFile]) -> Optional[str]:
    if url:
        # Simulasi penyimpanan file dan mendapatkan URL
        return f"https://example.com/files/{url.filename}"
    return None
