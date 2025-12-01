from core.log import logger
from models.OrganizerType import OrganizerType
from sqlalchemy.orm import Session

def insert_initial_organizer_types(db: Session) -> None:
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
