from datetime import datetime
import json
import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pytz import timezone
from sqlalchemy.orm import Session

from core.mux_service import mux_service
from core.responses import (
    BadRequest,
    InternalServerError,
    NoContent,
    NotFound,
    Ok,
    Unauthorized,
    common_response,
)
from core.security import get_user_from_token, oauth2_scheme
from models import get_db_sync
from models.StreamAsset import StreamStatus
from repository import streaming as streamingRepo
from schemas.common import (
    BadRequestResponse,
    InternalServerErrorResponse,
    NoContentResponse,
    NotFoundResponse,
    UnauthorizedResponse,
)
from schemas.streaming import (
    CreateLiveStreamRequest,
    LiveStreamResponse,
    PaginatedStreamListResponse,
    PlaybackURLResponse,
    StreamAnalyticsResponse,
    StreamAssetDetail,
    StreamAssetListItem,
    TrackViewRequest,
)
from settings import TZ

router = APIRouter(prefix="/streaming", tags=["Streaming"])


@router.post(
    "/live",
    responses={
        "200": {"model": LiveStreamResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def create_live_stream(
    request: CreateLiveStreamRequest,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        current_user = get_user_from_token(db=db, token=token)
        if current_user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        # TODO: Check if user has permission to create live streams

        (
            mux_stream_id,
            stream_key,
            stream_url,
            playback_id,
        ) = mux_service.create_live_stream(is_public=request.is_public)

        stream_asset = streamingRepo.create_stream_asset(
            db=db,
            title=request.title,
            description=request.description,
            is_public=request.is_public,
            is_live=True,
            schedule_id=request.schedule_id,
            mux_live_stream_id=mux_stream_id,
            mux_playback_id=playback_id,
            mux_signed_playback_id=playback_id if not request.is_public else None,
            status=StreamStatus.PENDING,
        )

        return common_response(
            Ok(
                data=LiveStreamResponse(
                    stream_id=stream_asset.id,
                    mux_stream_key=stream_key,
                    mux_stream_url=stream_url,
                    playback_url=None,
                    status=stream_asset.status,
                )
            )
        )
    except Exception as e:
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/{stream_id}/playback",
    responses={
        "200": {"model": PlaybackURLResponse},
        "400": {"model": BadRequestResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_playback_url(
    stream_id: UUID,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        current_user = get_user_from_token(db=db, token=token)
        if current_user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        stream_asset = streamingRepo.get_stream_asset_by_id(db, stream_id)
        if not stream_asset:
            return common_response(NotFound(message="Stream not found"))

        if stream_asset.status not in [
            StreamStatus.READY,
            StreamStatus.STREAMING,
            StreamStatus.ENDED,
        ]:
            return common_response(
                BadRequest(message="Stream is not ready for playback")
            )

        if not stream_asset.is_public and not current_user:
            return common_response(
                Unauthorized(message="Authentication required for private streams")
            )

        playback_id = (
            stream_asset.mux_signed_playback_id
            if not stream_asset.is_public
            else stream_asset.mux_playback_id
        )

        if not playback_id:
            return common_response(
                InternalServerError(error="Playback ID not available")
            )

        if stream_asset.is_public:
            playback_url = mux_service.get_public_playback_url(playback_id)
            thumbnail_url = mux_service.get_public_thumbnail_url(playback_id)
            token_expires_at = None
        else:
            playback_url, token_expires_at = mux_service.generate_signed_playback_url(
                playback_id, user_id=current_user.id
            )
            thumbnail_url, _ = mux_service.generate_signed_thumbnail_url(playback_id)

        return common_response(
            Ok(
                data=PlaybackURLResponse(
                    playback_url=playback_url,
                    thumbnail_url=thumbnail_url,
                    is_live=stream_asset.is_live,
                    status=stream_asset.status,
                    token_expires_at=token_expires_at,
                )
            )
        )
    except Exception as e:
        return common_response(InternalServerError(error=str(e)))


@router.post(
    "/{stream_id}/view",
    responses={
        "204": {"model": NoContentResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def track_view(
    stream_id: UUID,
    request_data: TrackViewRequest,
    req: Request,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        current_user = get_user_from_token(db=db, token=token)

        stream_asset = streamingRepo.get_stream_asset_by_id(db, stream_id)
        if not stream_asset:
            return common_response(NotFound(message="Stream not found"))

        if not stream_asset.is_public and not current_user:
            return common_response(
                Unauthorized(message="Authentication required for private streams")
            )

        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")

        streamingRepo.create_stream_view(
            db=db,
            stream_asset_id=stream_id,
            started_at=request_data.started_at,
            duration_watched=request_data.duration_watched,
            user_id=current_user.id if current_user else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        streamingRepo.increment_view_count(db, stream_asset)

        return common_response(NoContent())
    except HTTPException:
        raise
    except Exception as e:
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/{stream_id}/analytics",
    responses={
        "200": {"model": StreamAnalyticsResponse},
        "401": {"model": UnauthorizedResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_stream_analytics(
    stream_id: UUID,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        current_user = get_user_from_token(db=db, token=token)
        if current_user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        stream_asset = streamingRepo.get_stream_asset_by_id(db, stream_id)
        if not stream_asset:
            return common_response(NotFound(message="Stream not found"))

        analytics = streamingRepo.get_stream_analytics(db, stream_id)

        return common_response(Ok(data=StreamAnalyticsResponse(**analytics)))
    except Exception as e:
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/",
    responses={
        "200": {"model": PaginatedStreamListResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_streams(
    page: int = 1,
    limit: int = 20,
    is_public: Optional[bool] = None,
    is_live: Optional[bool] = None,
    status: Optional[StreamStatus] = None,
    db: Session = Depends(get_db_sync),
):
    try:
        skip = (page - 1) * limit

        # Get streams
        items, total = streamingRepo.list_stream_assets(
            db=db,
            skip=skip,
            limit=limit,
            is_public=is_public,
            is_live=is_live,
            status=status,
        )

        # Convert to response format
        stream_items = [
            StreamAssetListItem(
                id=item.id,
                title=item.title,
                is_public=item.is_public,
                is_live=item.is_live,
                status=item.status,
                thumbnail_url=item.thumbnail_url,
                view_count=item.view_count,
                duration=item.duration,
                stream_started_at=item.stream_started_at,
                created_at=item.created_at,
            )
            for item in items
        ]

        total_pages = math.ceil(total / limit) if total > 0 else 0

        return common_response(
            Ok(
                data=PaginatedStreamListResponse(
                    items=stream_items,
                    total=total,
                    page=page,
                    limit=limit,
                    total_pages=total_pages,
                )
            )
        )

    except Exception as e:
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/{stream_id}",
    responses={
        "200": {"model": StreamAssetDetail},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_stream_detail(
    stream_id: UUID,
    db: Session = Depends(get_db_sync),
):
    try:
        stream_asset = streamingRepo.get_stream_asset_by_id(db, stream_id)
        if not stream_asset:
            return common_response(NotFound(message="Stream not found"))

        return common_response(
            Ok(
                data=StreamAssetDetail(
                    id=stream_asset.id,
                    schedule_id=stream_asset.schedule_id,
                    title=stream_asset.title,
                    description=stream_asset.description,
                    is_public=stream_asset.is_public,
                    is_live=stream_asset.is_live,
                    status=stream_asset.status,
                    duration=stream_asset.duration,
                    thumbnail_url=stream_asset.thumbnail_url,
                    view_count=stream_asset.view_count,
                    max_concurrent_viewers=stream_asset.max_concurrent_viewers,
                    stream_started_at=stream_asset.stream_started_at,
                    stream_ended_at=stream_asset.stream_ended_at,
                    created_at=stream_asset.created_at,
                    updated_at=stream_asset.updated_at,
                )
            )
        )
    except Exception as e:
        return common_response(InternalServerError(error=str(e)))


@router.post("/webhooks/mux")
async def mux_webhook(request: Request, db: Session = Depends(get_db_sync)):
    try:
        payload = await request.body()
        signature = request.headers.get("Mux-Signature", "")

        if not mux_service.verify_webhook_signature(payload, signature, ""):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        webhook_data = json.loads(payload)
        event_type = webhook_data.get("type")
        data = webhook_data.get("data", {})

        if event_type == "video.asset.ready":
            asset_id = data.get("id")
            duration = data.get("duration")
            playback_ids = data.get("playback_ids", [])

            # Find stream asset by mux_asset_id
            stream_asset = streamingRepo.get_stream_asset_by_mux_id(
                db, asset_id, is_live=False
            )
            if stream_asset:
                # Update status and metadata
                update_data = {
                    "status": StreamStatus.READY,
                    "duration": int(duration) if duration else None,
                }
                if playback_ids:
                    update_data["mux_playback_id"] = playback_ids[0].get("id")
                    if playback_ids[0].get("policy") == "signed":
                        update_data["mux_signed_playback_id"] = playback_ids[0].get(
                            "id"
                        )

                streamingRepo.update_stream_asset(
                    db=db, stream_asset=stream_asset, **update_data
                )

        elif event_type == "video.asset.errored":
            # Video processing failed
            asset_id = data.get("id")
            stream_asset = streamingRepo.get_stream_asset_by_mux_id(
                db, asset_id, is_live=False
            )
            if stream_asset:
                streamingRepo.update_stream_asset(
                    db=db, stream_asset=stream_asset, status=StreamStatus.FAILED
                )

        elif event_type == "video.live_stream.active":
            # Live stream started
            stream_id = data.get("id")
            stream_asset = streamingRepo.get_stream_asset_by_mux_id(
                db, stream_id, is_live=True
            )
            if stream_asset:
                streamingRepo.update_stream_asset(
                    db=db,
                    stream_asset=stream_asset,
                    status=StreamStatus.STREAMING,
                    stream_started_at=datetime.now(timezone(TZ)),
                )

        elif event_type == "video.live_stream.idle":
            # Live stream stopped
            stream_id = data.get("id")
            stream_asset = streamingRepo.get_stream_asset_by_mux_id(
                db, stream_id, is_live=True
            )
            if stream_asset:
                duration = None
                if stream_asset.stream_started_at:
                    duration = int(
                        (
                            datetime.now(timezone(TZ)) - stream_asset.stream_started_at
                        ).total_seconds()
                    )

                streamingRepo.update_stream_asset(
                    db=db,
                    stream_asset=stream_asset,
                    status=StreamStatus.ENDED,
                    stream_ended_at=datetime.now(timezone(TZ)),
                    duration=duration,
                )

        return JSONResponse(content={"status": "success"})
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )
