from core.responses import handle_http_exception
import traceback
from core.log import logger
import traceback
from schemas.streaming import MuxStreamDetail
from models.User import MANAGEMENT_PARTICIPANT
from core.responses import Forbidden
from datetime import datetime
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pytz import timezone
from sqlalchemy.orm import Session

from core.mux_service import mux_service
from core.responses import (
    BadRequest,
    InternalServerError,
    NotFound,
    Ok,
    Unauthorized,
    common_response,
)
from core.security import get_user_from_token, oauth2_scheme
from models import get_db_sync
from models.Stream import StreamStatus
from repository import streaming as streamingRepo
from schemas.common import (
    BadRequestResponse,
    InternalServerErrorResponse,
    NotFoundResponse,
)
from schemas.streaming import (
    PlaybackURLResponse,
)
from settings import TZ

router = APIRouter(prefix="/streaming", tags=["Streaming"])


@router.get(
    "/{stream_id}",
    responses={
        "200": {"model": PlaybackURLResponse},
        "400": {"model": BadRequestResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_stream_playback(
    stream_id: UUID,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        current_user = get_user_from_token(db=db, token=token)
        if current_user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        stream_asset = streamingRepo.get_stream_by_id(db, stream_id)
        if not stream_asset:
            return common_response(NotFound(message="Stream not found"))

        if stream_asset.schedule.deleted_at:
            return common_response(NotFound(message="Stream not found"))

        if stream_asset.status not in [
            StreamStatus.STREAMING.value,
            StreamStatus.ENDED.value,
        ]:
            return common_response(
                BadRequest(message="Stream is not ready for playback")
            )

        playback_id = stream_asset.mux_playback_id
        if not playback_id:
            return common_response(
                InternalServerError(custom_response="Playback ID not available")
            )

        playback_token = None
        thumbnail_token = None
        token_expires_at = None
        if stream_asset.is_public:
            playback_url = mux_service.get_public_playback_url(playback_id)
            thumbnail_url = mux_service.get_public_thumbnail_url(playback_id)
        else:
            playback_token, playback_url, token_expires_at = (
                mux_service.generate_signed_playback_url(
                    playback_id, user_id=current_user.id
                )
            )
            thumbnail_token, thumbnail_url, _ = (
                mux_service.generate_signed_thumbnail_url(playback_id)
            )

        return common_response(
            Ok(
                data=PlaybackURLResponse(
                    playback=PlaybackURLResponse.Playback(
                        id=playback_id,
                        url=playback_url,
                        token=playback_token,
                    ),
                    thumbnail=PlaybackURLResponse.Thumbnail(
                        url=thumbnail_url,
                        token=thumbnail_token,
                    ),
                    metadata=PlaybackURLResponse.Metadata(
                        user_id=str(current_user.id),
                        title=stream_asset.schedule.title,
                    ),
                    status=stream_asset.status,
                    token_expires_at=token_expires_at,
                ).model_dump(mode="json")
            )
        )
    except HTTPException as e:
        return handle_http_exception(e)
    except Exception as e:
        traceback.print_exc()
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/{stream_id}/stream",
    responses={
        "200": {"model": MuxStreamDetail},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_mux_stream(
    stream_id: UUID,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        current_user = get_user_from_token(db=db, token=token)
        if current_user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if current_user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

        stream_asset = streamingRepo.get_stream_by_id(db, stream_id)
        if not stream_asset:
            return common_response(NotFound(message="Stream not found"))

        if stream_asset.schedule.deleted_at:
            return common_response(NotFound(message="Stream not found"))

        mux_stream = mux_service.get_live_stream(stream_asset.mux_live_stream_id)

        return common_response(Ok(data=mux_stream.model_dump()))
    except Exception as e:
        traceback.print_exc()
        return common_response(InternalServerError(error=str(e)))


@router.post("/webhook")
async def mux_webhook(request: Request, db: Session = Depends(get_db_sync)):
    try:
        payload = await request.body()
        signature = request.headers.get("Mux-Signature", "")

        if not mux_service.verify_webhook_signature(payload, signature, ""):
            return common_response(Unauthorized(message="Invalid webhook signature"))

        webhook_data = json.loads(payload)
        logger.info(f"Webhook Mux Data: {webhook_data}")
        event_type = webhook_data.get("type")
        data = webhook_data.get("data", {})

        if event_type == "video.live_stream.active":
            # Live stream started
            stream_id = data.get("id")
            stream_asset = streamingRepo.get_stream_by_mux_id(db, stream_id)
            if stream_asset:
                streamingRepo.update_stream(
                    db=db,
                    stream_asset=stream_asset,
                    status=StreamStatus.STREAMING,
                    stream_started_at=datetime.now(timezone(TZ)),
                )

        elif event_type == "video.live_stream.idle":
            # Live stream stopped
            stream_id = data.get("id")
            stream_asset = streamingRepo.get_stream_by_mux_id(db, stream_id)
            if stream_asset:
                duration = None
                if stream_asset.stream_started_at:
                    duration = int(
                        (
                            datetime.now(timezone(TZ)) - stream_asset.stream_started_at
                        ).total_seconds()
                    )

                streamingRepo.update_stream(
                    db=db,
                    stream_asset=stream_asset,
                    status=StreamStatus.ENDED,
                    stream_ended_at=datetime.now(timezone(TZ)),
                    duration=duration,
                )

        return common_response(Ok(data={"status": "success"}))
    except HTTPException:
        raise
    except Exception as e:
        return common_response(InternalServerError(error=str(e)))
