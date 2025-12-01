from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.log import logger
from schemas.auth import AuthorizationStatusEnum
from core.security import get_current_user, check_permissions
from models import get_db_sync
from models.User import MANAGEMENT_PARTICIPANT, User
from core.responses import (
    Ok,
    Forbidden,
    BadRequest,
    Unauthorized,
    InternalServerError,
    NotFound,
    common_response,
)
from schemas.organizer import OrganizerCreateRequest, organizer_response_item_from_model
from repository.user import get_user_by_id
from repository.organizer_type import get_organizer_type_by_id
from repository.organizer import insert_organizer, delete_organizer_data, get_organizer_by_id

router = APIRouter(prefix="/organizer", tags=["Organizer"])


@router.get("/")
def get_organizers(db: Session = Depends(get_db_sync)):
    logger.info("Fetching all organizers")
    pass


@router.post("/")
def create_organizer(
    create_request: OrganizerCreateRequest,
    db: Session = Depends(get_db_sync),
    current_user: User | None = Depends(get_current_user),
):
    logger.info("Creating a new organizer")
    auth_status = check_permissions(current_user, MANAGEMENT_PARTICIPANT)
    if auth_status == AuthorizationStatusEnum.UNAUTHORIZED:
        return common_response(Unauthorized(message="Unauthorized"))
    if auth_status == AuthorizationStatusEnum.FORBIDDEN:
        return common_response(
            Forbidden(custom_response="Forbidden: Insufficient permissions")
        )
    try:
        organizer_type = get_organizer_type_by_id(db, create_request.organizer_type_id)

        if not organizer_type:
            logger.error(
                f"Organizer type with ID {create_request.organizer_type_id} not found"
            )
            return common_response(NotFound(message="Organizer type not found"))

        user = get_user_by_id(db, create_request.user_id)
        if not user:
            logger.error(f"User with ID {create_request.user_id} not found")
            return common_response(NotFound(message="User not found"))
        new_organizer = insert_organizer(db, user, organizer_type)
        response = organizer_response_item_from_model(new_organizer)
        return common_response(Ok(data=response.model_dump()))
        logger.info(f"Organizer created with ID: {new_organizer.id}")
    except ValueError as ve:
        logger.error(f"Value error: User already an organizer of this type - {ve}")
        return common_response(BadRequest(custom_response="User already an organizer of this type"))
    except Exception as e:
        logger.error(f"Error creating organizer: {e}")
        return common_response(InternalServerError(error=str(e)))


@router.get("/{organizer_id}")
def find_organizer_by_id(organizer_id: str, db: Session = Depends(get_db_sync)):
    logger.info(f"Fetching organizer with ID: {organizer_id}")
    pass


@router.put("/{organizer_id}")
def update_organizer(
    organizer_id: str,
    db: Session = Depends(get_db_sync),
    current_user: User | None = Depends(get_current_user),
):
    logger.info(f"Updating organizer with ID: {organizer_id}")
    auth_status = check_permissions(current_user, MANAGEMENT_PARTICIPANT)
    if auth_status == AuthorizationStatusEnum.UNAUTHORIZED:
        return common_response(Unauthorized(message="Unauthorized"))
    if auth_status == AuthorizationStatusEnum.FORBIDDEN:
        return common_response(
            Forbidden(custom_response="Forbidden: Insufficient permissions")
        )


@router.delete("/{organizer_id}")
def delete_organizer(
    organizer_id: str,
    db: Session = Depends(get_db_sync),
    current_user: User | None = Depends(get_current_user),
):
    logger.info(f"Deleting organizer with ID: {organizer_id}")
    auth_status = check_permissions(current_user, MANAGEMENT_PARTICIPANT)
    if auth_status == AuthorizationStatusEnum.UNAUTHORIZED:
        return common_response(Unauthorized(message="Unauthorized"))
    if auth_status == AuthorizationStatusEnum.FORBIDDEN:
        return common_response(
            Forbidden(custom_response="Forbidden: Insufficient permissions")
        )
    try:
        organizer = get_organizer_by_id(id=organizer_id, db=db)
        if not organizer:
            logger.error(f"Organizer with ID {organizer_id} not found")
            return common_response(NotFound(message="Organizer not found"))
        delete_organizer_data(db, organizer)
        logger.info(f"Organizer with ID: {organizer_id} deleted successfully")
        return common_response(Ok(data={"message": "Organizer deleted successfully"}))
    except Exception as e:
        logger.error(f"Error deleting organizer: {e}")
        return common_response(InternalServerError(error=str(e)))


@router.get("/{organizer_id}/profile-picture")
def get_organizer_profile_picture(
    organizer_id: str, db: Session = Depends(get_db_sync)
):
    logger.info(f"Getting profile picture for organizer ID: {organizer_id}")
    pass
