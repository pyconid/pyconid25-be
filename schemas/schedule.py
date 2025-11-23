from models.Stream import StreamStatus
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID
from enum import Enum
from fastapi import Query
from pydantic import BaseModel, model_validator

from schemas.speaker import SpeakerResponseItem


class Language(str, Enum):
    ENGLISH = "English"
    BAHASA_INDONESIA = "Bahasa Indonesia"


class ScheduleQuery(BaseModel):
    page: int = Query(1, description="Page Number")
    page_size: int = Query(1, description="Page Size")
    schedule_date: Optional[date] = Query(None, description="Schedule Date")
    search: Optional[str] = Query(None, description="Search by title name")
    all: Optional[bool] = Query(None, description="Return all schedule data if true")


class CreateScheduleRequest(BaseModel):
    title: str
    speaker_id: UUID
    room_id: UUID
    schedule_type_id: UUID
    description: Optional[str] = None
    presentation_language: Optional[Language] = None
    slide_language: Optional[Language] = None
    slide_title: Optional[str] = None
    slide_link: Optional[str] = None
    tags: Optional[List[str]] = None
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def check_dates(self):
        if self.end < self.start:
            raise ValueError("End time must be not be less than start time")
        return self


class UpdateScheduleRequest(BaseModel):
    title: Optional[str] = None
    speaker_id: Optional[UUID] = None
    room_id: Optional[UUID] = None
    schedule_type_id: Optional[UUID] = None
    description: Optional[str] = None
    presentation_language: Optional[Language] = None
    slide_language: Optional[Language] = None
    slide_title: Optional[str] = None
    slide_link: Optional[str] = None
    tags: Optional[List[str]] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None

    @model_validator(mode="after")
    def check_dates(self):
        if self.start and self.end:
            if self.end < self.start:
                raise ValueError("End time must be not be less than start time")
        return self


class RoomInfo(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class ScheduleTypeInfo(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class StreamInfo(BaseModel):
    id: UUID
    status: StreamStatus

    model_config = {"from_attributes": True}


class ScheduleDetail(BaseModel):
    id: UUID
    title: str
    speaker: SpeakerResponseItem
    room: RoomInfo
    schedule_type: ScheduleTypeInfo
    description: Optional[str] = None
    presentation_language: Optional[Language] = None
    slide_language: Optional[Language] = None
    slide_title: Optional[str] = None
    slide_link: Optional[str] = None
    tags: Optional[List[str]] = None
    start: datetime
    end: datetime
    created_at: datetime
    updated_at: datetime
    stream: Optional[StreamInfo] = None

    model_config = {"from_attributes": True}


class ScheduleResponseItem(BaseModel):
    id: UUID
    title: str
    speaker: SpeakerResponseItem
    presentation_language: Optional[Language] = None
    tags: Optional[List[str]] = None
    start: datetime
    end: datetime
    created_at: datetime
    updated_at: datetime
    stream: Optional[StreamInfo] = None

    model_config = {"from_attributes": True}


class ScheduleResponse(BaseModel):
    page: int
    page_size: int
    count: int
    page_count: int
    results: List[ScheduleResponseItem]
