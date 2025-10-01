from sqlalchemy import UUID
from sqlalchemy.inspection import inspect
import datetime
from enum import Enum
from pydantic import HttpUrl
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.User import User
from schemas.user_profile import UserProfileDB


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    data = db.execute(stmt).scalar()
    return data


def update_user_profile(
    db: Session, user_id: UUID, profile_data: UserProfileDB
) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar()
    if user is None:
        return None
    valid_columns = {c.key for c in inspect(User).mapper.column_attrs}
    profile_data_dict = profile_data.model_dump()
    for key, value in profile_data_dict.items():
        if key not in valid_columns:
            continue

        # Convert Pydantic types to native
        if isinstance(value, HttpUrl):
            value = str(value)
        elif isinstance(value, Enum):
            value = value.value
        elif isinstance(value, list):
            value = ",".join(map(str, value))
        elif isinstance(value, datetime.date):
            value = value  # SQLAlchemy Date / DateTime accepts date object

        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user
