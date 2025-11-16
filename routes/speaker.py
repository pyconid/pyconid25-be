from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile
from pytz import timezone
from core.file import is_over_max_file_size, upload_file
from core.security import get_current_user
from models.User import MANAGEMENT_PARTICIPANT, User
from schemas.speaker import SpeakerDetailResponse, SpeakerQuery, SpeakerResponse
from sqlalchemy.orm import Session
from core.responses import (
    BadRequest,
    Forbidden,
    InternalServerError,
    NoContent,
    NotFound,
    Ok,
    common_response,
)
from models import get_db_sync
from schemas.common import (
    BadRequestResponse,
    ForbiddenResponse,
    InternalServerErrorResponse,
    NoContentResponse,
    NotFoundResponse,
    UnauthorizedResponse,
)
from repository import speaker as speakerRepo
from repository import speaker_type as speakerTypeRepo
from settings import MAX_FILE_SIZE_MB

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
    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    data = speakerRepo.get_speaker_by_id(db=db, id=id)
    if data is None:
        return common_response(NotFound(error=f"Speaker with {id} not found"))

    return common_response(
        Ok(
            data=SpeakerDetailResponse(
                id=str(data.id),
                name=data.name,
                bio=data.bio,
                photo_url=data.photo_url,
                email=data.email,
                instagram_link=data.instagram_link,
                x_link=data.x_link,
                created_at=data.created_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=data.updated_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                speaker_type=SpeakerDetailResponse.DetailSpeakerType(
                    id=str(data.speaker_type.id),
                    name=data.speaker_type.name,
                )
                if data.speaker_type
                else None,
            ).model_dump()
        )
    )


@router.post(
    "/",
    responses={
        "200": {"model": SpeakerDetailResponse},
        "400": {"model": BadRequestResponse},
        "403": {"model": ForbiddenResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def create_speaker(
    name: str = Form(),
    bio: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    email: Optional[str] = Form(None),
    instagram_link: Optional[str] = Form(None),
    x_link: Optional[str] = Form(None),
    speaker_type_id: Optional[str] = Form(None),
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    # Validation
    speaker_type = None
    if speaker_type_id:
        speaker_type = speakerTypeRepo.get_speaker_type_by_id(db=db, id=speaker_type_id)
        if speaker_type is None:
            return common_response(
                BadRequest(error=f"Speaker type with id {speaker_type_id} not found")
            )

    photo_url = None
    if photo is not None:
        if is_over_max_file_size(upload_file=photo):
            return common_response(
                BadRequest(
                    error=f"File size exceeds the maximum limit ({MAX_FILE_SIZE_MB} mb)"
                )
            )
        now = datetime.now().astimezone(timezone("Asia/Jakarta"))
        photo_url = (
            f"{name}-profile-photo-{now.strftime('%Y%m%d%H%M%S')}-{photo.filename}"
        )
        await upload_file(upload_file=photo, path=photo_url)

    new_speaker = speakerRepo.create_speaker(
        db=db,
        name=name,
        bio=bio,
        photo_url=photo_url,
        email=email,
        instagram_link=instagram_link,
        x_link=x_link,
        speaker_type=speaker_type,
        is_commit=True,
    )
    return common_response(
        Ok(
            data=SpeakerDetailResponse(
                id=str(new_speaker.id),
                name=new_speaker.name,
                bio=new_speaker.bio,
                photo_url=new_speaker.photo_url,
                email=new_speaker.email,
                instagram_link=new_speaker.instagram_link,
                x_link=new_speaker.x_link,
                created_at=new_speaker.created_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=new_speaker.updated_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                speaker_type=SpeakerDetailResponse.DetailSpeakerType(
                    id=str(new_speaker.speaker_type.id),
                    name=new_speaker.speaker_type.name,
                )
                if new_speaker.speaker_type
                else None,
            ).model_dump()
        )
    )


@router.put(
    "/{id}",
    responses={
        "200": {"model": SpeakerDetailResponse},
        "400": {"model": BadRequestResponse},
        "403": {"model": ForbiddenResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def update_speaker(
    id: str,
    name: str = Form(),
    bio: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    email: Optional[str] = Form(None),
    instagram_link: Optional[str] = Form(None),
    x_link: Optional[str] = Form(None),
    speaker_type_id: Optional[str] = Form(None),
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    existing_speaker = speakerRepo.get_speaker_by_id(db=db, id=id)
    if existing_speaker is None:
        return common_response(NotFound(error=f"Speaker with {id} not found"))

    # Validation
    speaker_type = None
    if speaker_type_id:
        speaker_type = speakerTypeRepo.get_speaker_type_by_id(db=db, id=speaker_type_id)
        if speaker_type is None:
            return common_response(
                BadRequest(error=f"Speaker type with id {speaker_type_id} not found")
            )

    photo_url = None
    if photo is not None:
        if is_over_max_file_size(upload_file=photo):
            return common_response(
                BadRequest(
                    error=f"File size exceeds the maximum limit ({MAX_FILE_SIZE_MB} mb)"
                )
            )
        now = datetime.now().astimezone(timezone("Asia/Jakarta"))
        photo_url = (
            f"{name}-profile-photo-{now.strftime('%Y%m%d%H%M%S')}-{photo.filename}"
        )
        await upload_file(upload_file=photo, path=photo_url)

    updated_speaker = speakerRepo.update_speaker(
        db=db,
        speaker=existing_speaker,
        name=name,
        bio=bio,
        photo_url=photo_url,
        email=email,
        instagram_link=instagram_link,
        x_link=x_link,
        speaker_type=speaker_type,
        is_commit=True,
    )
    return common_response(
        Ok(
            data=SpeakerDetailResponse(
                id=str(updated_speaker.id),
                name=updated_speaker.name,
                bio=updated_speaker.bio,
                photo_url=updated_speaker.photo_url,
                email=updated_speaker.email,
                instagram_link=updated_speaker.instagram_link,
                x_link=updated_speaker.x_link,
                created_at=updated_speaker.created_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=updated_speaker.updated_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                speaker_type=SpeakerDetailResponse.DetailSpeakerType(
                    id=str(updated_speaker.speaker_type.id),
                    name=updated_speaker.speaker_type.name,
                )
                if updated_speaker.speaker_type
                else None,
            ).model_dump()
        )
    )


@router.delete(
    "/{id}",
    responses={
        "204": {"model": NoContentResponse},
        "403": {"model": ForbiddenResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def delete_speaker_by_id(
    id: str, db: Session = Depends(get_db_sync), user: User = Depends(get_current_user)
):
    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    data = speakerRepo.get_speaker_by_id(db=db, id=id)
    if data is None:
        return common_response(NotFound(error=f"Speaker with {id} not found"))

    speakerRepo.delete_speaker(db=db, speaker=data, is_commit=True)

    return common_response(NoContent())
