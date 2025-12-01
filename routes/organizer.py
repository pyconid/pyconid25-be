from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import get_db_sync
from core.log import logger
router = APIRouter(prefix="/organizer", tags=["Organizer"])



@router.get(
    "/")
def get_organizers(db: Session = Depends(get_db_sync)):
    logger.info("Fetching all organizers")
    pass

@router.post("/")
def create_organizer(db: Session = Depends(get_db_sync)):
    logger.info("Creating a new organizer")
    pass

@router.get("/{organizer_id}")
def get_organizer_by_id(organizer_id: str, db: Session = Depends(get_db_sync)):
    logger.info(f"Fetching organizer with ID: {organizer_id}")
    pass

@router.put("/{organizer_id}")
def update_organizer(organizer_id: str, db: Session = Depends(get_db_sync)):
    logger.info(f"Updating organizer with ID: {organizer_id}")
    pass

@router.delete("/{organizer_id}")
def delete_organizer(organizer_id: str, db: Session = Depends(get_db_sync)):
    logger.info(f"Deleting organizer with ID: {organizer_id}")
    pass

@router.get("/{organizer_id}/profile-picture")
def get_organizer_profile_picture(organizer_id: str, db: Session = Depends(get_db_sync)):
    logger.info(f"Getting profile picture for organizer ID: {organizer_id}")
    pass

