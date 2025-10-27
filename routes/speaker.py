from fastapi import APIRouter, Depends
from schemas.speaker import SpeakerQuery, SpeakerResponse
from sqlalchemy.orm import Session
from core.responses import (
    InternalServerError,
    common_response,
)
from models import get_db_sync
from schemas.common import (
    InternalServerErrorResponse,
)
from repository import speaker as speakerRepo

router = APIRouter(prefix="/speaker", tags=["Speaker"])


@router.get(
    "/",
    responses={
        "200": {"model": SpeakerResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_speaker(
    query: SpeakerQuery = Depends(), db: Session = Depends(get_db_sync)
):
    try:
        if query.all:
            data = speakerRepo.get_all_speakers(db=db)
        else:
            data = speakerRepo.get_speaker_per_page_by_search(
                db=db,
                page=query.page,
                page_size=query.page_size,
                search=query.search,
            )
    except Exception as e:
        return common_response(InternalServerError(error=str(e)))
    return SpeakerResponse.model_validate(data)
