from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.User import User


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    data = db.execute(stmt).scalar()
    return data
