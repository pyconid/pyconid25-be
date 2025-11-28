from typing import Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from schemas.user_profile import ParticipantType, TShirtSize
from models.User import User

class CheckinUserResponse(BaseModel):
    id: str = Field(..., description="User ID")
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    t_shirt_size: Optional[TShirtSize] = None
    participant_type: Optional[ParticipantType] = None
    checked_in_day1: bool = False
    checked_in_day2: bool = False
    
    
def user_model_to_checkin_response(user: User) -> CheckinUserResponse:
    """Convert User model to CheckinUserResponse schema

    Args:
        user (User): User model instance

    Returns:
        CheckinUserResponse: CheckinUserResponse schema instance
    """
    return CheckinUserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        t_shirt_size=user.t_shirt_size if isinstance(user.t_shirt_size, TShirtSize) else None,
        participant_type=user.participant_type if isinstance(user.participant_type, ParticipantType) else None,
        checked_in_day1=user.attendance_day_1,
        checked_in_day2=user.attendance_day_2,
    )

class CheckinDayEnum(str, Enum):
    day1 = "day1"
    day2 = "day2"

class CheckinUserRequest(BaseModel):
    payment_id: str = Field(
        description="Payment ID associated with the user"
    )
    
    day: CheckinDayEnum = Field(
        description="The day for which the user is checking in. The value can be 'day1' or 'day2'."
    )