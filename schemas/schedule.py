from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, model_validator

from models.Stream import StreamStatus
from schemas.speaker_type import DetailSpeakerResponse


class Language(str, Enum):
    ENGLISH = "English"
    BAHASA_INDONESIA = "Bahasa Indonesia"


class ScheduleQuery(BaseModel):
    page: Optional[int] = Query(1, description="Page Number")
    page_size: Optional[int] = Query(1, description="Page Size")
    schedule_date: Optional[date] = Query(None, description="Schedule Date")
    search: Optional[str] = Query(None, description="Search by title name")
    all: Optional[bool] = Query(None, description="Return all schedule data if true")


class CreateScheduleRequest(BaseModel):
    title: str
    speaker_id: Optional[UUID] = None
    room_id: UUID
    schedule_type_id: UUID
    description: Optional[str] = None
    presentation_language: Optional[Language] = None
    slide_language: Optional[Language] = None
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
    title: str
    speaker_id: Optional[UUID] = None
    room_id: UUID
    schedule_type_id: UUID
    description: Optional[str] = None
    presentation_language: Optional[Language] = None
    slide_language: Optional[Language] = None
    slide_link: Optional[str] = None
    tags: Optional[List[str]] = None
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def check_dates(self):
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


class PublicSpeakerUser(BaseModel):
    id: UUID
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    # phone: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    job_category: Optional[str] = None
    job_title: Optional[str] = None
    website: Optional[str] = None
    facebook_username: Optional[str] = None
    linkedin_username: Optional[str] = None
    twitter_username: Optional[str] = None
    instagram_username: Optional[str] = None

    model_config = {"from_attributes": True}


class PublicSpeakerInfo(BaseModel):
    id: UUID
    user: PublicSpeakerUser
    speaker_type: Optional[DetailSpeakerResponse] = None
    model_config = {"from_attributes": True}


class PublicScheduleDetail(BaseModel):
    id: UUID
    title: str
    speaker: Optional[PublicSpeakerInfo] = None
    room: RoomInfo
    schedule_type: ScheduleTypeInfo
    description: Optional[str] = None
    presentation_language: Optional[Language] = None
    slide_language: Optional[Language] = None
    slide_link: Optional[str] = None
    tags: Optional[List[str]] = None
    start: datetime
    end: datetime
    created_at: datetime
    updated_at: datetime
    stream: Optional[StreamInfo] = None

    model_config = {"from_attributes": True}


class SimplePublicSpeakerUser(BaseModel):
    id: UUID
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    model_config = {"from_attributes": True}


class SimplePublicSpeakerInfo(BaseModel):
    id: UUID
    user: SimplePublicSpeakerUser
    speaker_type: Optional[DetailSpeakerResponse] = None
    model_config = {"from_attributes": True}


class ScheduleDetail(BaseModel):
    id: UUID
    title: str
    speaker: Optional[SimplePublicSpeakerInfo] = None
    room: RoomInfo
    schedule_type: ScheduleTypeInfo
    description: Optional[str] = None
    presentation_language: Optional[Language] = None
    slide_language: Optional[Language] = None
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
    speaker: Optional[SimplePublicSpeakerInfo] = None
    room: RoomInfo
    schedule_type: ScheduleTypeInfo
    presentation_language: Optional[Language] = None
    tags: Optional[List[str]] = None
    start: datetime
    end: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScheduleResponse(BaseModel):
    page: int
    page_size: int
    count: int
    page_count: int
    results: List[ScheduleResponseItem]


class MuxStreamDetail(BaseModel):
    stream_id: str
    status: str
    stream_key: str
    playback_id: str
    model_config = {"extra": "allow"}


class ScheduleCMSResponseItem(BaseModel):
    id: str
    title: str
    speaker: Optional[SimplePublicSpeakerInfo] = None
    room: RoomInfo
    schedule_type: ScheduleTypeInfo
    stream_key: Optional[str] = None
    start: datetime
    end: datetime


class ScheduleCMSResponse(BaseModel):
    page: int
    page_size: int
    count: int
    page_count: int
    results: List[ScheduleCMSResponseItem]
