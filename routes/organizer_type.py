from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.responses import Ok, common_response, InternalServerError
from schemas.common import (
    InternalServerErrorResponse,
)
from models import get_db_sync
from schemas.organizer_type import OrganizerTypeAllResponse, organizer_type_all_response_from_models
from repository.organizer_type import get_all_organizer_types
from core.log import logger
router = APIRouter(prefix="/organizer-type", tags=["Organizer Type"])
@router.get(
    "/",
    responses={
        "200": {"model": OrganizerTypeAllResponse},
        "500": {"model": InternalServerErrorResponse}
    },
)
async def get_speaker(db: Session = Depends(get_db_sync)):
    try:
        all_speaker_types = get_all_organizer_types(db=db)
        response = organizer_type_all_response_from_models(all_speaker_types)
        return common_response(Ok(data=response.model_dump()))
    except Exception as e:
        logger.error(f"Error retrieving organizer types: {e}")
        return common_response(InternalServerError(error=str(e)))
    