from sqlalchemy import select
from models.Room import Room
from sqlalchemy.orm import Session


def initial_room(db: Session, is_commit: bool = True):
    rooms = [
        Room(id="019ab02a-c155-7c32-9e9a-8131f4b60447", name="Auditorium"),
        Room(
            id="019ab02a-e899-7bf8-9296-c7a959f38ac3", name="Classroom #1"
        ),
        Room(
            id="019ab02b-0b7d-7e33-82d8-46f3592f07dd", name="Classroom #2"
        ),
        Room(
            id="019ab02b-27b2-7d02-9f95-07dc8dd9a9ab", name="Classroom #3"
        ),
    ]

    for room in rooms:
        stmt = select(Room).where(Room.id == room.id)
        existing = db.execute(stmt).scalar()
        if not existing:
            db.add(room)
        else:
            existing.name = room.name

    if is_commit:
        db.commit()
