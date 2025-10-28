from typing import List, Optional
from fastapi import Query
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class SpeakerQuery(BaseModel):
    page: int = Query(1, description="Page Number")
    page_size: int = Query(1, description="Page Size")
    search: Optional[str] = Query(None, description="Search by speaker name")
    all: Optional[bool] = Query(None, description="Return all speaker if true")


class SpeakerResponseItem(BaseModel):
    id: UUID
    name: str
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    email: Optional[str] = None
    instagram_link: Optional[str] = None
    x_link: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_keynote_speaker: Optional[bool] = None
    model_config = {
        "from_attributes": True  # ⬅️ penting biar bisa baca dari SQLAlchemy ORM object
    }


class SpeakerResponse(BaseModel):
    page: int
    page_size: int
    count: int
    page_count: int
    results: List[SpeakerResponseItem]
