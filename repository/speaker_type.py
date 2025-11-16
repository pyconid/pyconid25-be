from typing import Optional
from sqlalchemy import select
from models.SpeakerType import SpeakerType
from sqlalchemy.orm import Session


def get_all_speaker_types(db: Session) -> list[SpeakerType]:
    stmt = select(SpeakerType).order_by(SpeakerType.name.asc())
    return db.execute(stmt).scalars().all()


def get_speaker_type_by_id(db: Session, id: str) -> Optional[SpeakerType]:
    stmt = select(SpeakerType).where(SpeakerType.id == id)
    return db.execute(stmt).scalar()
