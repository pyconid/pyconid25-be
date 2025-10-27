from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import Query
from pydantic import BaseModel

from schemas.speaker import SpeakerResponseItem


class ScheduleQuery(BaseModel):
    page: int = Query(1, description="Page Number")
    page_size: int = Query(1, description="Page Size")
    search: Optional[str] = Query(None, description="Search by topic name")
    all: Optional[bool] = Query(None, description="Return all schedule data if true")


class ScheduleResponseItem(BaseModel):
    id: UUID
    topic: str
    speaker: SpeakerResponseItem
    desciption: Optional[str] = None
    stream_link: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {
        "from_attributes": True  # penting biar bisa baca dari SQLAlchemy ORM object
    }


class ScheduleResponse(BaseModel):
    page: int
    page_size: int
    count: int
    page_count: int
    results: List[ScheduleResponseItem]
