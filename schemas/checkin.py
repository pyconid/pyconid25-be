from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from schemas.user_profile import ParticipantType, TShirtSize


class CheckinUserResponse(BaseModel):
    id: str = Field(..., description="User ID")
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    t_shirt_size: Optional[TShirtSize] = None
    participant_type: Optional[ParticipantType] = None
    checked_in_day1: bool = False
    checked_in_day2: bool = False
