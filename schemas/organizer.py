from pydantic import BaseModel
from typing import Optional, Literal

from fastapi import Query
from models.Organizer import Organizer


class OrganizerQuery(BaseModel):
    page: int = Query(1, description="Page Number")
    page_size: int = Query(1, description="Page Size")
    search: Optional[str] = Query(None, description="Search by speaker name")
    all: Optional[bool] = Query(None, description="Return all speaker if true")
    order_dir: Literal["asc", "desc"] = Query(
        "asc", description="Order direction: asc or desc"
    )


class OrganizerDetailUser(BaseModel):
    id: str
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    bio: str | None = None
    profile_picture: str | None = None
    email: str | None = None
    instagram_username: str | None = None
    twitter_username: str | None = None


class OrganizerDetailType(BaseModel):
    id: str
    name: str


class OrganizerDetailResponse(BaseModel):
    id: str
    user: OrganizerDetailUser
    organizer_type: OrganizerDetailType
    created_at: str | None = None
    updated_at: str | None = None


class OrganizerCreateRequest(BaseModel):
    user_id: str
    organizer_type_id: str


class OrganizerUpdateRequest(BaseModel):
    user_id: str | None = None
    organizer_type_id: str | None = None


class OrganizerResponseItem(BaseModel):
    id: str
    user_id: str
    organizer_type_id: str
    created_at: str | None = None
    updated_at: str | None = None


class OrganizersByType(BaseModel):
    organizer_type: OrganizerDetailType
    organizers: list[OrganizerDetailUser]


class OrganizersByTypeAll(BaseModel):
    results: list[OrganizersByType]


def organizer_response_item_from_model(organizer: Organizer) -> OrganizerResponseItem:
    """Convert Organizer ORM model to OrganizerResponseItem Pydantic model."""
    return OrganizerResponseItem(
        id=str(organizer.id),
        user_id=str(organizer.user_id),
        organizer_type_id=str(organizer.organizer_type_id),
        created_at=organizer.created_at.isoformat() if organizer.created_at else None,
        updated_at=organizer.updated_at.isoformat() if organizer.updated_at else None,
    )
