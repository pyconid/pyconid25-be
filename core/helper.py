from datetime import datetime
from fastapi import UploadFile
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

def save_file_and_get_url(url: Optional[UploadFile]) -> Optional[str]:
    if url:
        # Simulasi penyimpanan file dan mendapatkan URL
        return f"{url.filename}-{datetime.now().timestamp()}"
    return None

def get_current_time_in_timezone(timezone_str: str = "Asia/Jakarta") -> datetime:
    """Get Current Time in Specified Timezone

    Args:
        timezone_str (str): Timezone string (e.g., "Asia/Jakarta")

    Returns:
        datetime: Current datetime in the specified timezone
    """
    try:
        tz = ZoneInfo(timezone_str)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    return datetime.now(tz)