from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session
from models.Organizer import Organizer
from models.OrganizerType import OrganizerType
from models.User import User
from core.helper import get_current_time_in_timezone
from settings import TZ
from core.log import logger

def insert_organizer(db: Session, user: User, organizer_type: OrganizerType) -> Organizer:
    try:
        logger.info("Creating organizer in the database")
        
        existing = db.execute(
            select(Organizer).where(
                (Organizer.user_id == user.id) & 
                (Organizer.organizer_type_id == organizer_type.id)
            )
        ).scalar()
        
        if existing:
            logger.warning(f"Organizer already exists for user {user.id} with type {organizer_type.id}")
            raise ValueError(f"User {user.id} is already an organizer of type {organizer_type.id}")
        
        current_datetime = get_current_time_in_timezone(TZ)
        new_organizer = Organizer(
            user=user,
            organizer_type=organizer_type,
            created_at=current_datetime,
            updated_at=current_datetime,
        )
        db.add(new_organizer)
        db.commit()
        db.refresh(new_organizer)
        logger.info(f"Organizer created with ID: {new_organizer.id}")
        return new_organizer
    except IntegrityError as e:
        logger.error(f"Integrity constraint violation: {e}")
        db.rollback()
        raise ValueError("User and organizer type combination already exists")
    except Exception as e:
        logger.error(f"Error creating organizer: {e}")
        db.rollback()
        raise e
    
def get_organizer_by_id(db: Session, id: str) -> Organizer | None:
    stmt = select(Organizer).where(Organizer.id == id)
    return db.execute(stmt).scalar()

def delete_organizer_data(db: Session, organizer: Organizer) -> None:
    logger.info(f"Deleting organizer with ID: {organizer.id}")
    try:
        db.delete(organizer)
        db.commit()
        logger.info(f"Organizer with ID: {organizer.id} deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting organizer with ID: {organizer.id} - {e}")
        db.rollback()
        raise e