from typing import Union
from uuid import UUID
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.Room import Room


def get_rooms(db: Session, search: Optional[str] = None) -> list[Room]:
    stmt = select(Room).where(Room.deleted_at.is_(None))

    if search:
        stmt = stmt.where(Room.name.ilike(f"%{search}%"))

    stmt = stmt.order_by(Room.name)

    return list(db.execute(stmt).scalars().all())

def get_room_by_id(db: Session, room_id: Union[UUID, str]) -> Optional[Room]:
    stmt = select(Room).where(Room.id == room_id)
    return db.execute(stmt).scalar_one_or_none()
