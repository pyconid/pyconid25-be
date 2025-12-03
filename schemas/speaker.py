from typing import List, Literal, Optional
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel

from schemas.schedule import PublicSpeakerInfo
from schemas.speaker_type import DetailSpeakerResponse


class SpeakerQuery(BaseModel):
    page: int = Query(1, description="Page Number")
    page_size: int = Query(1, description="Page Size")
    search: Optional[str] = Query(None, description="Search by speaker name")
    all: Optional[bool] = Query(None, description="Return all speaker if true")
    order_dir: Literal["asc", "desc"] = Query(
        "asc", description="Order direction: asc or desc"
    )


class UserInSpeakerResponse(BaseModel):
    id: UUID
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

    model_config = {"from_attributes": True}


class SpeakerResponseItem(BaseModel):
    id: UUID
    user: UserInSpeakerResponse
    speaker_type: Optional[DetailSpeakerResponse] = None
    model_config = {"from_attributes": True}


class SpeakerResponse(BaseModel):
    page: int
    page_size: int
    count: int
    page_count: int
    results: List[SpeakerResponseItem]


class AllSpeakerResponse(BaseModel):
    results: List[PublicSpeakerInfo]


class SpeakerDetailResponse(BaseModel):
    id: str

    class DetailUser(BaseModel):
        id: str
        first_name: Optional[str] = None
        last_name: Optional[str] = None
        username: Optional[str] = None
        bio: Optional[str] = None
        profile_picture: Optional[str] = None
        email: str = None
        instagram_username: Optional[str] = None
        twitter_username: Optional[str] = None

    user: DetailUser
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class DetailSpeakerType(BaseModel):
        id: str
        name: str

    speaker_type: Optional[DetailSpeakerType] = None


class CreateSpeakerRequest(BaseModel):
    user_id: str
    speaker_type_id: Optional[str] = None


class CreateSpeakerResponse(BaseModel):
    id: str
    user_id: str
    speaker_type_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UpdateSpeakerRequest(BaseModel):
    user_id: str
    speaker_type_id: Optional[str] = None


class UpdateSpeakerResponse(BaseModel):
    id: str
    user_id: str
    speaker_type_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
