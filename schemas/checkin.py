from typing import Optional
from enum import Enum
from core.log import logger
from pydantic import BaseModel, EmailStr, Field
from models.User import User


class CheckinUserResponse(BaseModel):
    id: str = Field(..., description="User ID")
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    t_shirt_size: Optional[str] = None
    participant_type: Optional[str] = None
    checked_in_day1: bool = False
    checked_in_day2: bool = False


class CheckinUserResponseSchema(BaseModel):
    data: CheckinUserResponse
    message: str = "User check-in data retrieved successfully"


def user_model_to_checkin_response(user: User) -> CheckinUserResponse:
    """Convert User model to CheckinUserResponse schema

    Args:
        user (User): User model instance

    Returns:
        CheckinUserResponse: CheckinUserResponse schema instance
    """
    tshirt_size = None
    participant_type = None
    try:
        tshirt_size = user.t_shirt_size
        participant_type = user.participant_type
    except ValueError as e:
        logger.error(f"Invalid enum value in user model: {e}")

    return CheckinUserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        t_shirt_size=tshirt_size,
        participant_type=participant_type,
        checked_in_day1=user.attendance_day_1,
        checked_in_day2=user.attendance_day_2,
    )


class CheckinDayEnum(str, Enum):
    day1 = "day1"
    day2 = "day2"


class CheckinUserRequest(BaseModel):
    payment_id: str = Field(description="Payment ID associated with the user")

    day: CheckinDayEnum = Field(
        description="The day for which the user is checking in. The value can be 'day1' or 'day2'."
    )
