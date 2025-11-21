from sqlalchemy import select
from models.SpeakerType import SpeakerType
from sqlalchemy.orm import Session


def initial_speaker_type(db: Session, is_commit: bool = True):
    speaker_types = [
        SpeakerType(id="019a8a01-295e-7aa0-8424-53966527cb9c", name="Keynote Speaker"),
        SpeakerType(
            id="019a8a01-5984-7bde-b8cb-94c19fed292b", name="Regular Talk Speaker"
        ),
        SpeakerType(
            id="019a8a01-9677-7f7c-b540-970076a55e1a", name="Short Talk Speaker"
        ),
    ]

    for speaker_type in speaker_types:
        stmt = select(SpeakerType).where(SpeakerType.id == speaker_type.id)
        existing = db.execute(stmt).scalar()
        if not existing:
            db.add(speaker_type)
        else:
            existing.name = speaker_type.name

    if is_commit:
        db.commit()
