from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Sequence
from core.log import logger
from models.OrganizerType import OrganizerType


def insert_initial_organizer_types(db: Session) -> None:
    """Insert predefined organizer types into the database."""
    logger.info("Inserting initial organizer types...")
    try:
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
        logger.info("Initial organizer types inserted successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to insert initial organizer types: {e}")
        raise


def get_all_organizer_types(db: Session) -> Sequence[OrganizerType]:
    """Retrieve all organizer types from the database."""
    stmt =select(OrganizerType).order_by(OrganizerType.name.asc())
    return db.execute(stmt).scalars().all()

def get_organizer_type_by_id(db: Session, id: str) -> OrganizerType | None:
    """Retrieve an organizer type by its ID."""
    stmt = select(OrganizerType).where(OrganizerType.id == id)
    return db.execute(stmt).scalar()