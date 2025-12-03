from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from pytz import timezone
from core.file import get_file
from core.security import get_current_user
from models.User import MANAGEMENT_PARTICIPANT, User
from schemas.volunteer import (
    CreateVolunteerRequest,
    CreateVolunteerResponse,
    UserInVolunteerResponse,
    VolunteerDetailResponse,
    VolunteerQuery,
    VolunteerResponse,
    UpdateVolunteerRequest,
    UpdateVolunteerResponse,
    VolunteerResponseItem,
    VolunteerUserResponse,
)
from sqlalchemy.orm import Session
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
from models import get_db_sync
from schemas.common import (
    BadRequestResponse,
    ForbiddenResponse,
    InternalServerErrorResponse,
    NoContentResponse,
    NotFoundResponse,
    UnauthorizedResponse,
)
from repository import volunteer as volunteerRepo
from repository import user as userRepo

router = APIRouter(prefix="/volunteer", tags=["Volunteer"])


@router.get(
    "/public/",
    responses={
        "200": {"model": VolunteerResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_volunteer_public(
    query: VolunteerQuery = Depends(), db: Session = Depends(get_db_sync)
):
    try:
        data = volunteerRepo.get_all_volunteers(
            db=db, order_dir=query.order_dir, search=query.search
        )
        return common_response(
            Ok(
                data=VolunteerResponse(
                    results=[
                        VolunteerResponseItem(
                            id=str(volunteer.id),
                            user=UserInVolunteerResponse(
                                id=str(volunteer.user.id),
                                username=volunteer.user.username,
                                first_name=volunteer.user.first_name,
                                last_name=volunteer.user.last_name,
                                email=volunteer.user.email,
                                website=volunteer.user.website
                                if volunteer.user.share_my_public_social_media
                                else None,
                                facebook_username=volunteer.user.facebook_username
                                if volunteer.user.share_my_public_social_media
                                else None,
                                linkedin_username=volunteer.user.linkedin_username
                                if volunteer.user.share_my_public_social_media
                                else None,
                                twitter_username=volunteer.user.twitter_username
                                if volunteer.user.share_my_public_social_media
                                else None,
                                instagram_username=volunteer.user.instagram_username
                                if volunteer.user.share_my_public_social_media
                                else None,
                                profile_picture=volunteer.user.profile_picture,
                            ),
                        )
                        for volunteer in data
                    ]
                ).model_dump()
            )
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/",
    responses={
        "200": {"model": VolunteerResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_volunteer(
    query: VolunteerQuery = Depends(),
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    try:
        if user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

        data = volunteerRepo.get_all_volunteers(
            db=db, order_dir=query.order_dir, search=query.search
        )
        return common_response(
            Ok(
                data=VolunteerResponse(
                    results=[
                        VolunteerResponseItem(
                            id=str(volunteer.id),
                            user=UserInVolunteerResponse(
                                id=str(volunteer.user.id),
                                username=volunteer.user.username,
                                first_name=volunteer.user.first_name,
                                last_name=volunteer.user.last_name,
                                email=volunteer.user.email,
                                website=volunteer.user.website
                                if volunteer.user.share_my_public_social_media
                                else None,
                                facebook_username=volunteer.user.facebook_username
                                if volunteer.user.share_my_public_social_media
                                else None,
                                linkedin_username=volunteer.user.linkedin_username
                                if volunteer.user.share_my_public_social_media
                                else None,
                                twitter_username=volunteer.user.twitter_username
                                if volunteer.user.share_my_public_social_media
                                else None,
                                instagram_username=volunteer.user.instagram_username
                                if volunteer.user.share_my_public_social_media
                                else None,
                                profile_picture=volunteer.user.profile_picture,
                            ),
                        )
                        for volunteer in data
                    ]
                ).model_dump()
            )
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/{id}",
    responses={
        "200": {"model": VolunteerDetailResponse},
        "401": {"model": UnauthorizedResponse},
        "403": {"model": ForbiddenResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_volunteer_by_id(
    id: str, db: Session = Depends(get_db_sync), user: User = Depends(get_current_user)
):
    if user is None:
        return common_response(Unauthorized(message="Unauthorized"))

    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    data = volunteerRepo.get_volunteer_by_id(db=db, id=id)
    if data is None:
        return common_response(NotFound(error=f"Volunteer with {id} not found"))

    return common_response(
        Ok(
            data=VolunteerDetailResponse(
                id=str(data.id),
                user=VolunteerDetailResponse.DetailUser(
                    id=str(data.user.id),
                    first_name=data.user.first_name,
                    last_name=data.user.last_name,
                    username=data.user.username,
                    bio=data.user.bio,
                    email=data.user.email,
                    facebook_username=data.user.facebook_username
                    if data.user.share_my_public_social_media
                    else None,
                    linkedin_username=data.user.linkedin_username
                    if data.user.share_my_public_social_media
                    else None,
                    twitter_username=data.user.twitter_username
                    if data.user.share_my_public_social_media
                    else None,
                    instagram_username=data.user.instagram_username
                    if data.user.share_my_public_social_media
                    else None,
                    profile_picture=data.user.profile_picture,
                ),
            ).model_dump()
        )
    )


@router.post(
    "/",
    responses={
        "200": {"model": CreateVolunteerResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "403": {"model": ForbiddenResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def create_volunteer(
    request: CreateVolunteerRequest,
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    if user is None:
        return common_response(Unauthorized(message="Unauthorized"))

    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    # Validation
    user = userRepo.get_user_by_id(db=db, id=request.user_id)
    if user is None:
        return common_response(
            BadRequest(message=f"User with id {request.user_id} not found")
        )

    volunteer = volunteerRepo.get_volunteer_by_user_id(db=db, user_id=request.user_id)
    if volunteer is not None:
        return common_response(
            BadRequest(
                message=f"Volunteer for user id {request.user_id} already exists"
            )
        )

    now = datetime.now().astimezone(timezone("Asia/Jakarta"))
    new_volunteer = volunteerRepo.create_volunteer(
        db=db,
        user=user,
        now=now,
        is_commit=True,
    )
    return common_response(
        Ok(
            data=CreateVolunteerResponse(
                id=str(new_volunteer.id),
                user_id=str(new_volunteer.user.id),
                created_at=new_volunteer.created_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=new_volunteer.updated_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
            ).model_dump()
        )
    )


@router.put(
    "/{id}",
    responses={
        "200": {"model": UpdateVolunteerResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "403": {"model": ForbiddenResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def update_volunteer(
    id: str,
    request: UpdateVolunteerRequest,
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    if user is None:
        return common_response(Unauthorized(message="Unauthorized"))

    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    existing_volunteer = volunteerRepo.get_volunteer_by_id(db=db, id=id)
    if existing_volunteer is None:
        return common_response(NotFound(message=f"Volunteer with {id} not found"))

    # Validation
    user = userRepo.get_user_by_id(db=db, id=request.user_id)
    if user is None:
        return common_response(
            BadRequest(message=f"User with id {request.user_id} not found")
        )

    volunteer = volunteerRepo.get_volunteer_by_user_id(
        db=db, user_id=request.user_id, exclude_user_id=existing_volunteer.user_id
    )
    if volunteer is not None:
        return common_response(
            BadRequest(
                message=f"Volunteer for user id {request.user_id} already exists"
            )
        )

    updated_volunteer = volunteerRepo.update_volunteer(
        db=db,
        volunteer=existing_volunteer,
        user=user,
        is_commit=True,
    )
    return common_response(
        Ok(
            data=UpdateVolunteerResponse(
                id=str(updated_volunteer.id),
                user_id=str(updated_volunteer.user.id),
                created_at=updated_volunteer.created_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=updated_volunteer.updated_at.astimezone(
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
async def delete_volunteer_by_id(
    id: str, db: Session = Depends(get_db_sync), user: User = Depends(get_current_user)
):
    if user is None:
        return common_response(Unauthorized(message="Unauthorized"))

    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    data = volunteerRepo.get_volunteer_by_id(db=db, id=id)
    if data is None:
        return common_response(NotFound(message=f"Volunteer with {id} not found"))

    volunteerRepo.delete_volunteer(db=db, volunteer=data, is_commit=True)

    return common_response(NoContent())


@router.get("/{id}/profile-picture/", response_class=FileResponse)
async def get_volunteer_profile_picture(id: str, db: Session = Depends(get_db_sync)):
    data = volunteerRepo.get_volunteer_by_id(db=db, id=id)
    if data is None or data.user.profile_picture is None:
        return common_response(
            NotFound(message=f"Profile picture for volunteer with {id} not found")
        )

    photo = get_file(path=data.user.profile_picture)
    if photo is None:
        return common_response(
            NotFound(error=f"Profile picture file for volunteer with {id} not found")
        )

    return photo


@router.get(
    "/user/",
    responses={
        "200": {"model": VolunteerUserResponse},
        "401": {"model": ForbiddenResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_user_volunteers(
    search: Optional[str] = None,
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    if user is None:
        return common_response(Unauthorized(message="Unauthorized"))

    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    all_user = userRepo.get_user_for_volunteer(db=db, search=search)
    return common_response(
        Ok(
            data=VolunteerUserResponse(
                results=[
                    VolunteerUserResponse.DetailUser(
                        id=str(user.id),
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        email=user.email,
                    )
                    for user in all_user
                ]
            ).model_dump()
        )
    )
