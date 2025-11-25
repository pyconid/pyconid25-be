import traceback
from schemas.common import ForbiddenResponse
from models.User import MANAGEMENT_PARTICIPANT
from core.responses import Forbidden
from schemas.common import BadRequestResponse
from core.responses import BadRequest
from core.log import logger
from uuid import UUID
from fastapi import APIRouter, Depends
from schemas.schedule import (
    CreateScheduleRequest,
    MuxStreamDetail,
    PublicScheduleDetail,
    RoomInfo,
    ScheduleCMSResponse,
    ScheduleCMSResponseItem,
    ScheduleDetail,
    ScheduleQuery,
    ScheduleResponse,
    ScheduleTypeInfo,
    SimplePublicSpeakerInfo,
    UpdateScheduleRequest,
)
from sqlalchemy.orm import Session
from core.responses import (
    Created,
    InternalServerError,
    NoContent,
    NotFound,
    Ok,
    Unauthorized,
    common_response,
)
from core.security import get_user_from_token, oauth2_scheme
from core.mux_service import mux_service
from models import get_db_sync
from models.Stream import StreamStatus
from schemas.common import (
    InternalServerErrorResponse,
    NoContentResponse,
    NotFoundResponse,
    UnauthorizedResponse,
)
from repository import (
    schedule as scheduleRepo,
    streaming as streamingRepo,
    room as roomRepo,
    speaker as speakerRepo,
    schedule_type as scheduleTypeRepo,
)

router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.post(
    "/",
    responses={
        "201": {"model": ScheduleDetail},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "403": {"model": ForbiddenResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def create_schedule(
    request: CreateScheduleRequest,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    mux_stream_id = None
    try:
        current_user = get_user_from_token(db=db, token=token)
        if current_user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if current_user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

        room = roomRepo.get_room_by_id(db=db, room_id=request.room_id)
        if room is None:
            return common_response(BadRequest(message="Room not found"))

        schedule_type = scheduleTypeRepo.get_schedule_type_by_id(
            db=db, schedule_type_id=request.schedule_type_id
        )
        if schedule_type is None:
            return common_response(BadRequest(message="Schedule type not found"))

        speaker = speakerRepo.get_speaker_by_id(db=db, id=str(request.speaker_id))
        if speaker is None:
            return common_response(BadRequest(message="Speaker not found"))

        # Create schedule
        schedule = scheduleRepo.create_schedule(
            db=db,
            title=request.title,
            speaker_id=request.speaker_id,
            room_id=request.room_id,
            schedule_type_id=request.schedule_type_id,
            description=request.description,
            presentation_language=request.presentation_language,
            slide_language=request.slide_language,
            slide_link=request.slide_link,
            tags=request.tags,
            start=request.start,
            end=request.end,
        )

        # Create Mux live stream for this schedule
        try:
            (
                mux_stream_id,
                stream_key,
                playback_id,
            ) = mux_service.create_live_stream(is_public=True)

            # Create stream asset linked to this schedule
            streamingRepo.create_stream(
                db=db,
                is_public=True,
                schedule_id=schedule.id,
                mux_live_stream_id=mux_stream_id,
                mux_playback_id=playback_id,
                mux_stream_key=stream_key,
                status=StreamStatus.PENDING,
            )
        except Exception as stream_error:
            logger.error(
                f"Failed to create stream for schedule {schedule.id}: {stream_error}"
            )

        # Refresh to get all relationships
        db.refresh(schedule)

        return common_response(
            Created(
                data=ScheduleDetail.model_validate(schedule).model_dump(mode="json")
            )
        )

    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        if mux_stream_id is not None:
            mux_service.delete_live_stream(mux_stream_id)
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/cms",
    responses={
        "200": {"model": ScheduleCMSResponse},
        "403": {"model": ForbiddenResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_schedule_cms(
    query: ScheduleQuery = Depends(),
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        current_user = get_user_from_token(db=db, token=token)
        if current_user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        data, num_data, num_page = scheduleRepo.get_schedule_cms(
            db=db,
            page=query.page,
            page_size=query.page_size,
            search=query.search,
            schedule_date=query.schedule_date,
            all=query.all,
        )

        return common_response(
            Ok(
                data=ScheduleCMSResponse(
                    count=num_data,
                    page_size=(
                        query.page_size if not query.all and query.page_size else 0
                    ),
                    page=(query.page if not query.all and query.page else 1),
                    page_count=(
                        num_page if not query.all and num_page is not None else 1
                    ),
                    results=[
                        ScheduleCMSResponseItem(
                            id=str(r.id),
                            title=r.title,
                            speaker=SimplePublicSpeakerInfo.model_validate(r.speaker),
                            room=RoomInfo.model_validate(r.room),
                            schedule_type=ScheduleTypeInfo.model_validate(
                                r.schedule_type
                            ),
                            stream_key=(
                                r.stream.mux_stream_key
                                if r.stream is not None
                                else None
                            ),
                            start=r.start,
                            end=r.end,
                        )
                        for r in data
                    ],
                ).model_dump(mode="json")
            )
        )
    except Exception as e:
        logger.error(f"Failed to get schedule cms: {e}")
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/{schedule_id}",
    responses={
        "200": {"model": PublicScheduleDetail},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_schedule_by_id(
    schedule_id: UUID,
    db: Session = Depends(get_db_sync),
):
    try:
        schedule = scheduleRepo.get_schedule_by_id(db, schedule_id)
        if not schedule:
            return common_response(NotFound(message="Schedule not found"))

        schedule_dict = PublicScheduleDetail.model_validate(schedule).model_dump(
            mode="json"
        )

        # Filter user data based on privacy settings
        user = schedule.speaker.user
        user_dict = schedule_dict["speaker"]["user"]

        filtered_user = {
            "id": user_dict["id"],
            "username": user_dict["username"],
            "first_name": user_dict.get("first_name"),
            "last_name": user_dict.get("last_name"),
            "bio": user_dict.get("bio"),
        }

        if user.share_my_email_and_phone_number:
            filtered_user["email"] = user_dict.get("email")
            filtered_user["phone"] = user_dict.get("phone")
        else:
            filtered_user["email"] = None
            filtered_user["phone"] = None

        if user.share_my_job_and_company:
            filtered_user["company"] = user_dict.get("company")
            filtered_user["job_category"] = user_dict.get("job_category")
            filtered_user["job_title"] = user_dict.get("job_title")
        else:
            filtered_user["company"] = None
            filtered_user["job_category"] = None
            filtered_user["job_title"] = None

        if user.share_my_public_social_media:
            filtered_user["website"] = user_dict.get("website")
            filtered_user["facebook_username"] = user_dict.get("facebook_username")
            filtered_user["linkedin_username"] = user_dict.get("linkedin_username")
            filtered_user["twitter_username"] = user_dict.get("twitter_username")
            filtered_user["instagram_username"] = user_dict.get("instagram_username")
        else:
            filtered_user["website"] = None
            filtered_user["facebook_username"] = None
            filtered_user["linkedin_username"] = None
            filtered_user["twitter_username"] = None
            filtered_user["instagram_username"] = None

        schedule_dict["speaker"]["user"] = filtered_user

        return common_response(Ok(data=schedule_dict))
    except Exception as e:
        logger.error(f"Failed to get schedule by id {schedule_id}: {e}")
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/{schedule_id}/stream",
    responses={
        "200": {"model": MuxStreamDetail},
        "403": {"model": ForbiddenResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_mux_stream_by_schedule_id(
    schedule_id: UUID,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        current_user = get_user_from_token(db=db, token=token)
        if current_user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if current_user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

        stream_asset = streamingRepo.get_stream_by_schedule_id(db, schedule_id)
        if not stream_asset:
            return common_response(NotFound(message="Stream not found"))

        if stream_asset.schedule.deleted_at:
            return common_response(NotFound(message="Stream not found"))

        return common_response(
            Ok(
                data=MuxStreamDetail(
                    stream_id=str(stream_asset.id),
                    status=stream_asset.status,
                    stream_key=stream_asset.mux_stream_key,
                    playback_id=stream_asset.mux_playback_id,
                ).model_dump(mode="json")
            )
        )
    except Exception as e:
        traceback.print_exc()
        return common_response(InternalServerError(error=str(e)))


@router.put(
    "/{schedule_id}",
    responses={
        "200": {"model": ScheduleDetail},
        "401": {"model": UnauthorizedResponse},
        "403": {"model": ForbiddenResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def update_schedule(
    schedule_id: UUID,
    request: UpdateScheduleRequest,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        current_user = get_user_from_token(db=db, token=token)
        if current_user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if current_user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

        schedule = scheduleRepo.get_schedule_by_id(db, schedule_id)
        if not schedule:
            return common_response(NotFound(message="Schedule not found"))

        if request.room_id is not None:
            room = roomRepo.get_room_by_id(db=db, room_id=request.room_id)
            if room is None:
                return common_response(BadRequest(message="Room not found"))

        if request.schedule_type_id is not None:
            schedule_type = scheduleTypeRepo.get_schedule_type_by_id(
                db=db, schedule_type_id=request.schedule_type_id
            )
            if schedule_type is None:
                return common_response(BadRequest(message="Schedule type not found"))

        if request.speaker_id is not None:
            speaker = speakerRepo.get_speaker_by_id(db=db, id=str(request.speaker_id))
            if speaker is None:
                return common_response(BadRequest(message="Speaker not found"))

        if request.end is not None:
            start_time = schedule.start
            if request.start is not None:
                start_time = request.start

            if request.end < start_time:
                return common_response(
                    BadRequest(message="End time must be after start time")
                )

        update_data = request.model_dump(exclude_unset=True)
        updated_schedule = scheduleRepo.update_schedule(db, schedule, **update_data)

        return common_response(
            Ok(
                data=ScheduleDetail.model_validate(updated_schedule).model_dump(
                    mode="json"
                )
            )
        )
    except Exception as e:
        logger.error(f"Failed to update schedule by id {schedule_id}: {e}")
        return common_response(InternalServerError(error=str(e)))


@router.post(
    "/{schedule_id}/recreate-stream",
    responses={
        "204": {"model": NoContentResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "403": {"model": ForbiddenResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def recreate_stream(
    schedule_id: UUID,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    mux_stream_id = None
    old_mux_stream_id = None
    try:
        current_user = get_user_from_token(db=db, token=token)
        if current_user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if current_user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

        schedule = scheduleRepo.get_schedule_by_id(db, schedule_id)
        if not schedule:
            return common_response(NotFound(message="Schedule not found"))

        if schedule.deleted_at:
            return common_response(NotFound(message="Schedule not found"))

        stream_asset = streamingRepo.get_stream_by_schedule_id(db, schedule_id)
        if stream_asset is not None:
            if stream_asset.status == StreamStatus.STREAMING:
                return common_response(
                    BadRequest(message="Stream is currently streaming")
                )

            old_mux_stream_id = stream_asset.mux_live_stream_id
            streamingRepo.delete_stream(db, stream_asset)

        # Create new Mux stream
        (
            mux_stream_id,
            stream_key,
            playback_id,
        ) = mux_service.create_live_stream(is_public=True)

        # Create stream asset linked to this schedule
        streamingRepo.create_stream(
            db=db,
            is_public=True,
            schedule_id=schedule.id,
            mux_live_stream_id=mux_stream_id,
            mux_playback_id=playback_id,
            mux_stream_key=stream_key,
            status=StreamStatus.PENDING,
        )

        if old_mux_stream_id is not None:
            try:
                mux_service.delete_live_stream(old_mux_stream_id)
            except Exception as cleanup_error:
                logger.warning(
                    f"Failed to cleanup old stream {old_mux_stream_id}: {cleanup_error}"
                )

        return common_response(NoContent())
    except Exception as e:
        logger.error(f"Failed to recreate stream for schedule {schedule_id}: {e}")
        if mux_stream_id is not None:
            try:
                mux_service.delete_live_stream(mux_stream_id)
            except Exception as rollback_error:
                logger.error(
                    f"Failed to rollback Mux stream {mux_stream_id}: {rollback_error}"
                )
        return common_response(InternalServerError(error=str(e)))


@router.delete(
    "/{schedule_id}",
    responses={
        "204": {"model": NoContentResponse},
        "401": {"model": UnauthorizedResponse},
        "403": {"model": ForbiddenResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def delete_schedule(
    schedule_id: UUID,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        current_user = get_user_from_token(db=db, token=token)
        if current_user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if current_user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

        schedule = scheduleRepo.get_schedule_by_id(db, schedule_id)
        if not schedule:
            return common_response(NotFound(message="Schedule not found"))
        mux_stream_id = None
        if schedule.stream:
            mux_stream_id = schedule.stream.mux_live_stream_id

        scheduleRepo.delete_schedule(db, schedule)

        if mux_stream_id:
            mux_service.delete_live_stream(mux_stream_id)

        return common_response(NoContent())
    except Exception as e:
        logger.error(f"Failed to delete schedule by id {schedule_id}: {e}")
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/",
    responses={
        "200": {"model": ScheduleResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_schedule(
    query: ScheduleQuery = Depends(), db: Session = Depends(get_db_sync)
):
    try:
        if query.all:
            data = scheduleRepo.get_all_schedules(
                db=db,
                search=query.search,
                schedule_date=query.schedule_date,
            )
        else:
            data = scheduleRepo.get_schedule_per_page_by_search(
                db=db,
                page=query.page if query.page else 1,
                page_size=query.page_size if query.page_size else 10,
                search=query.search,
                schedule_date=query.schedule_date,
            )
    except Exception as e:
        logger.error(f"Failed to get schedule: {e}")
        return common_response(InternalServerError(error=str(e)))
    return ScheduleResponse.model_validate(data)
