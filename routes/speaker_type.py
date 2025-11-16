from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.responses import Ok, common_response
from models import get_db_sync
from schemas.common import InternalServerErrorResponse
from schemas.speaker_type import SpeakerTypeAllResponse
from repository import speaker_type as speakerTypeRepo


router = APIRouter(prefix="/speaker-type", tags=["Speaker Type"])


@router.get(
    "/",
    responses={
        "200": {"model": SpeakerTypeAllResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_speaker(db: Session = Depends(get_db_sync)):
    all_speaker_types = speakerTypeRepo.get_all_speaker_types(db=db)
    return common_response(
        Ok(
            data=SpeakerTypeAllResponse(
                results=[
                    SpeakerTypeAllResponse.SpeakerTypeItem(
                        id=str(speaker_type.id), name=speaker_type.name
                    )
                    for speaker_type in all_speaker_types
                ]
            ).model_dump()
        )
    )
