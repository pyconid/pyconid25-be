from typing import List, Literal, Optional
from fastapi import Query
from pydantic import BaseModel


class VolunteerQuery(BaseModel):
    search: Optional[str] = Query(None, description="Search by speaker name")
    order_dir: Literal["asc", "desc"] = Query(
        "asc", description="Order direction: asc or desc"
    )


class UserInVolunteerResponse(BaseModel):
    id: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    facebook_username: Optional[str] = None
    linkedin_username: Optional[str] = None
    twitter_username: Optional[str] = None
    instagram_username: Optional[str] = None
    profile_picture: Optional[str] = None

    model_config = {"from_attributes": True}


class VolunteerResponseItem(BaseModel):
    id: str
    user: UserInVolunteerResponse


class VolunteerResponse(BaseModel):
    results: List[VolunteerResponseItem]


class VolunteerDetailResponse(BaseModel):
    id: str

    class DetailUser(BaseModel):
        id: str
        first_name: Optional[str] = None
        last_name: Optional[str] = None
        username: Optional[str] = None
        bio: Optional[str] = None
        profile_picture: Optional[str] = None
        email: str = None
        website: Optional[str] = None
        facebook_username: Optional[str] = None
        linkedin_username: Optional[str] = None
        twitter_username: Optional[str] = None
        instagram_username: Optional[str] = None
        profile_picture: Optional[str] = None

    user: DetailUser
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreateVolunteerRequest(BaseModel):
    user_id: str


class CreateVolunteerResponse(BaseModel):
    id: str
    user_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UpdateVolunteerRequest(BaseModel):
    user_id: str


class UpdateVolunteerResponse(BaseModel):
    id: str
    user_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
