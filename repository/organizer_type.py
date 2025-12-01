from typing import Optional
from sqlalchemy import select
from models.OrganizerType import OrganizerType
from sqlalchemy.orm import Session

def insert_initial_organizer_types(db: Session) -> None:
    initial_types = [
        OrganizerType(name="Lead Organizer"),
        OrganizerType(name="Field Coordinator"),
        OrganizerType(name="Programs"),
        OrganizerType(name="Website"),
        OrganizerType(name="Participant Experience"),
        OrganizerType(name="Logistics"),
        OrganizerType(name="Creative"),
    ]
    db.add_all(initial_types)
    db.commit()