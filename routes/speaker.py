from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from pytz import timezone
from sqlalchemy.orm import Session

from core.file import get_file
from core.log import logger
from core.responses import (
    BadRequest,
    Forbidden,
    InternalServerError,
    NoContent,
    NotFound,
    Ok,
    Unauthorized,
    common_response,
)
from core.security import get_current_user
from models import get_db_sync
from models.User import MANAGEMENT_PARTICIPANT, User
from repository import schedule as scheduleRepo
from repository import speaker as speakerRepo
from repository import speaker_type as speakerTypeRepo
from repository import user as userRepo
from schemas.common import (
    BadRequestResponse,
    ForbiddenResponse,
    InternalServerErrorResponse,
    NoContentResponse,
    NotFoundResponse,
    UnauthorizedResponse,
)
from schemas.schedule import PublicScheduleDetail, PublicSpeakerInfo
from schemas.speaker import (
    AllSpeakerResponse,
    CreateSpeakerRequest,
    CreateSpeakerResponse,
    SpeakerDetailResponse,
    SpeakerQuery,
    SpeakerResponse,
    UpdateSpeakerRequest,
    UpdateSpeakerResponse,
)

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
            data = speakerRepo.get_all_speakers(db=db, order_dir=query.order_dir)
        else:
            data = speakerRepo.get_speaker_per_page_by_search(
                db=db,
                page=query.page,
                page_size=query.page_size,
                search=query.search,
                order_dir=query.order_dir,
            )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return common_response(InternalServerError(error=str(e)))
    return SpeakerResponse.model_validate(data)


@router.get(
    "/public",
    responses={
        "200": {"model": AllSpeakerResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_speaker_public(db: Session = Depends(get_db_sync)):
    try:
        speakers = speakerRepo.get_all_speakers_public(db=db)

        speaker_schemas: list[PublicSpeakerInfo] = [
            PublicSpeakerInfo.model_validate(s) for s in speakers
        ]

        return common_response(
            Ok(data=AllSpeakerResponse(results=speaker_schemas).model_dump(mode="json"))
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/{id}",
    responses={
        "200": {"model": SpeakerDetailResponse},
        "401": {"model": UnauthorizedResponse},
        "403": {"model": ForbiddenResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_speaker_by_id(
    id: str, db: Session = Depends(get_db_sync), user: User = Depends(get_current_user)
):
    if user is None:
        return common_response(Unauthorized(message="Unauthorized"))

    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    data = speakerRepo.get_speaker_by_id(db=db, id=id)
    if data is None:
        return common_response(NotFound(message=f"Speaker with {id} not found"))

    return common_response(
        Ok(
            data=SpeakerDetailResponse(
                id=str(data.id),
                user=SpeakerDetailResponse.DetailUser(
                    id=str(data.user.id),
                    first_name=data.user.first_name,
                    last_name=data.user.last_name,
                    username=data.user.username,
                    bio=data.user.bio,
                    profile_picture=data.user.profile_picture,
                    email=data.user.email,
                    instagram_username=data.user.instagram_username,
                    twitter_username=data.user.twitter_username,
                ),
                speaker_type=SpeakerDetailResponse.DetailSpeakerType(
                    id=str(data.speaker_type.id),
                    name=data.speaker_type.name,
                )
                if data.speaker_type
                else None,
            ).model_dump()
        )
    )


@router.get(
    "/{id}/schedule/",
    responses={
        "200": {"model": PublicScheduleDetail},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_schedule_by_speaker(
    id: UUID,
    db: Session = Depends(get_db_sync),
):
    try:
        schedule = scheduleRepo.get_schedule_by_speaker_id(db, id)
        if not schedule:
            return common_response(NotFound(message="Speaker schedule not found"))

        return common_response(
            Ok(
                data=PublicScheduleDetail.model_validate(schedule).model_dump(
                    mode="json"
                )
            )
        )
    except Exception as e:
        logger.error(f"Failed to get schedule by id {id}: {e}")
        return common_response(InternalServerError(error=str(e)))


@router.post(
    "/",
    responses={
        "200": {"model": CreateSpeakerResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "403": {"model": ForbiddenResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def create_speaker(
    request: CreateSpeakerRequest,
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    if user is None:
        return common_response(Unauthorized(message="Unauthorized"))

    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    # Validation
    speaker_type = None
    if request.speaker_type_id:
        speaker_type = speakerTypeRepo.get_speaker_type_by_id(
            db=db, id=request.speaker_type_id
        )
        if speaker_type is None:
            return common_response(
                BadRequest(
                    message=f"Speaker type with id {request.speaker_type_id} not found"
                )
            )

    user = userRepo.get_user_by_id(db=db, id=request.user_id)
    if user is None:
        return common_response(
            BadRequest(message=f"User with id {request.user_id} not found")
        )

    now = datetime.now().astimezone(timezone("Asia/Jakarta"))
    new_speaker = speakerRepo.create_speaker(
        db=db,
        user=user,
        speaker_type=speaker_type,
        now=now,
        is_commit=True,
    )
    return common_response(
        Ok(
            data=CreateSpeakerResponse(
                id=str(new_speaker.id),
                user_id=str(new_speaker.user.id),
                speaker_type_id=str(new_speaker.speaker_type.id)
                if new_speaker.speaker_type
                else None,
                created_at=new_speaker.created_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=new_speaker.updated_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
            ).model_dump()
        )
    )


@router.put(
    "/{id}",
    responses={
        "200": {"model": UpdateSpeakerResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "403": {"model": ForbiddenResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def update_speaker(
    id: str,
    request: UpdateSpeakerRequest,
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    if user is None:
        return common_response(Unauthorized(message="Unauthorized"))

    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    existing_speaker = speakerRepo.get_speaker_by_id(db=db, id=id)
    if existing_speaker is None:
        return common_response(NotFound(message=f"Speaker with {id} not found"))

    # Validation
    speaker_type = None
    if request.speaker_type_id:
        speaker_type = speakerTypeRepo.get_speaker_type_by_id(
            db=db, id=request.speaker_type_id
        )
        if speaker_type is None:
            return common_response(
                BadRequest(
                    message=f"Speaker type with id {request.speaker_type_id} not found"
                )
            )

    user = userRepo.get_user_by_id(db=db, id=request.user_id)
    if user is None:
        return common_response(
            BadRequest(message=f"User with id {request.user_id} not found")
        )

    updated_speaker = speakerRepo.update_speaker(
        db=db,
        speaker=existing_speaker,
        user=user,
        speaker_type=speaker_type,
        is_commit=True,
    )
    return common_response(
        Ok(
            data=UpdateSpeakerResponse(
                id=str(updated_speaker.id),
                user_id=str(updated_speaker.user.id),
                speaker_type_id=str(updated_speaker.speaker_type.id)
                if updated_speaker.speaker_type
                else None,
                created_at=updated_speaker.created_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=updated_speaker.updated_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
            ).model_dump()
        )
    )


@router.delete(
    "/{id}",
    responses={
        "204": {"model": NoContentResponse},
        "401": {"model": UnauthorizedResponse},
        "403": {"model": ForbiddenResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def delete_speaker_by_id(
    id: str, db: Session = Depends(get_db_sync), user: User = Depends(get_current_user)
):
    if user is None:
        return common_response(Unauthorized(message="Unauthorized"))

    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    data = speakerRepo.get_speaker_by_id(db=db, id=id)
    if data is None:
        return common_response(NotFound(message=f"Speaker with {id} not found"))

    speakerRepo.delete_speaker(db=db, speaker=data, is_commit=True)

    return common_response(NoContent())


@router.get("/{id}/profile-picture/", response_class=FileResponse)
async def get_speaker_profile_picture(id: str, db: Session = Depends(get_db_sync)):
    data = speakerRepo.get_speaker_by_id(db=db, id=id)
    if data is None or data.user.profile_picture is None:
        return common_response(
            NotFound(message=f"Profile picture for speaker with {id} not found")
        )

    photo = get_file(path=data.user.profile_picture)
    if photo is None:
        return common_response(
            NotFound(message=f"Profile picture file for speaker with {id} not found")
        )

    return photo
