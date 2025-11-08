"""
Repository layer for streaming-related database operations
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from uuid import UUID

from pytz import timezone
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from models.StreamAsset import StreamAsset, StreamStatus
from models.StreamView import StreamView
from settings import TZ


def create_stream_asset(
    db: Session,
    title: str,
    is_public: bool = True,
    is_live: bool = False,
    description: Optional[str] = None,
    schedule_id: Optional[Union[UUID, str]] = None,
    mux_asset_id: Optional[str] = None,
    mux_playback_id: Optional[str] = None,
    mux_signed_playback_id: Optional[str] = None,
    mux_live_stream_id: Optional[str] = None,
    status: StreamStatus = StreamStatus.PENDING,
) -> StreamAsset:
    stream_asset = StreamAsset(
        title=title,
        description=description,
        is_public=is_public,
        is_live=is_live,
        schedule_id=schedule_id,
        mux_asset_id=mux_asset_id,
        mux_playback_id=mux_playback_id,
        mux_signed_playback_id=mux_signed_playback_id,
        mux_live_stream_id=mux_live_stream_id,
        status=status,
    )

    db.add(stream_asset)
    db.commit()
    db.refresh(stream_asset)

    return stream_asset


def get_stream_asset_by_id(
    db: Session, stream_id: Union[UUID, str], include_deleted: bool = False
) -> Optional[StreamAsset]:
    stmt = select(StreamAsset).where(StreamAsset.id == stream_id)

    if not include_deleted:
        stmt = stmt.where(StreamAsset.deleted_at.is_(None))

    return db.execute(stmt).scalar_one_or_none()


def get_stream_asset_by_mux_id(
    db: Session, mux_id: str, is_live: bool = False
) -> Optional[StreamAsset]:
    if is_live:
        stmt = select(StreamAsset).where(
            and_(
                StreamAsset.mux_live_stream_id == mux_id,
                StreamAsset.deleted_at.is_(None),
            )
        )
    else:
        stmt = select(StreamAsset).where(
            and_(StreamAsset.mux_asset_id == mux_id, StreamAsset.deleted_at.is_(None))
        )

    return db.execute(stmt).scalar_one_or_none()


def list_stream_assets(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    is_public: Optional[bool] = None,
    is_live: Optional[bool] = None,
    status: Optional[StreamStatus] = None,
) -> tuple[list[StreamAsset], int]:
    stmt = select(StreamAsset).where(StreamAsset.deleted_at.is_(None))

    if is_public is not None:
        stmt = stmt.where(StreamAsset.is_public == is_public)
    if is_live is not None:
        stmt = stmt.where(StreamAsset.is_live == is_live)
    if status is not None:
        stmt = stmt.where(StreamAsset.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one_or_none() or 0

    stmt = stmt.order_by(StreamAsset.created_at.desc()).offset(skip).limit(limit)

    items = db.execute(stmt).scalars().all()

    return list(items), total


def update_stream_asset(
    db: Session, stream_asset: StreamAsset, **kwargs
) -> StreamAsset:
    for key, value in kwargs.items():
        if hasattr(stream_asset, key):
            setattr(stream_asset, key, value)

    stream_asset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(stream_asset)

    return stream_asset


def delete_stream_asset(db: Session, stream_asset: StreamAsset) -> None:
    stream_asset.deleted_at = datetime.utcnow()
    db.commit()


def increment_view_count(db: Session, stream_asset: StreamAsset) -> StreamAsset:
    stream_asset.view_count += 1
    db.commit()
    db.refresh(stream_asset)

    return stream_asset


def create_stream_view(
    db: Session,
    stream_asset_id: Union[UUID, str],
    started_at: datetime,
    duration_watched: int,
    user_id: Optional[Union[UUID, str]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> StreamView:
    stream_view = StreamView(
        stream_asset_id=stream_asset_id,
        user_id=user_id,
        started_at=started_at,
        duration_watched=duration_watched,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(stream_view)
    db.commit()
    db.refresh(stream_view)

    return stream_view


def get_stream_analytics(db: Session, stream_asset_id: Union[UUID, str]) -> dict:
    total_views = (
        db.execute(
            select(func.count(StreamView.id)).where(
                StreamView.stream_asset_id == stream_asset_id
            )
        ).scalar()
        or 0
    )

    unique_viewers = (
        db.execute(
            select(func.count(func.distinct(StreamView.user_id))).where(
                and_(
                    StreamView.stream_asset_id == stream_asset_id,
                    StreamView.user_id.is_not(None),
                )
            )
        ).scalar()
        or 0
    )

    avg_watch_time = (
        db.execute(
            select(func.avg(StreamView.duration_watched)).where(
                StreamView.stream_asset_id == stream_asset_id
            )
        ).scalar()
        or 0
    )

    total_watch_time = (
        db.execute(
            select(func.sum(StreamView.duration_watched)).where(
                StreamView.stream_asset_id == stream_asset_id
            )
        ).scalar()
        or 0
    )

    views_by_date = db.execute(
        select(
            func.date(StreamView.started_at).label("date"),
            func.count(StreamView.id).label("views"),
        )
        .where(StreamView.stream_asset_id == stream_asset_id)
        .group_by(func.date(StreamView.started_at))
        .order_by(func.date(StreamView.started_at))
    ).all()

    stream_asset = get_stream_asset_by_id(db, stream_asset_id)
    max_concurrent_viewers = stream_asset.max_concurrent_viewers if stream_asset else 0

    return {
        "total_views": total_views or 0,
        "unique_viewers": unique_viewers or 0,
        "max_concurrent_viewers": max_concurrent_viewers,
        "average_watch_time": int(avg_watch_time),
        "total_watch_time": int(total_watch_time),
        "views_by_date": [
            {"date": str(row.date), "views": row.views} for row in views_by_date
        ],
    }


def get_active_viewers_count(db: Session, stream_asset_id: Union[UUID, str]) -> int:
    five_minutes_ago = datetime.now(timezone(TZ)) - timedelta(minutes=5)

    count = (
        db.execute(
            select(func.count(StreamView.id)).where(
                and_(
                    StreamView.stream_asset_id == stream_asset_id,
                    StreamView.started_at >= five_minutes_ago,
                    StreamView.ended_at.is_(None),
                )
            )
        ).scalar()
        or 0
    )

    return count
