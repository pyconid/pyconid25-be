from datetime import datetime
from typing import Optional, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.Stream import Stream, StreamStatus


def create_stream(
    db: Session,
    is_public: bool = True,
    schedule_id: Optional[Union[UUID, str]] = None,
    mux_playback_id: Optional[str] = None,
    mux_live_stream_id: Optional[str] = None,
    mux_stream_key: Optional[str] = None,
    status: StreamStatus = StreamStatus.PENDING,
) -> Stream:
    now = datetime.now()
    stream = Stream(
        is_public=is_public,
        schedule_id=schedule_id,
        mux_playback_id=mux_playback_id,
        mux_live_stream_id=mux_live_stream_id,
        mux_stream_key=mux_stream_key,
        status=status,
        created_at=now,
        updated_at=now,
    )

    db.add(stream)
    db.commit()
    db.refresh(stream)

    return stream


def get_stream_by_id(db: Session, stream_id: Union[UUID, str]) -> Optional[Stream]:
    stmt = select(Stream).where(Stream.id == stream_id)
    return db.execute(stmt).scalar_one_or_none()


def get_stream_by_mux_id(db: Session, mux_id: str) -> Optional[Stream]:
    stmt = select(Stream).where(Stream.mux_live_stream_id == mux_id)
    return db.execute(stmt).scalar_one_or_none()


def get_stream_by_mux_asset_id(db: Session, asset_id: str) -> Optional[Stream]:
    stmt = select(Stream).where(Stream.mux_asset_id == asset_id)
    return db.execute(stmt).scalar_one_or_none()


def get_stream_by_schedule_id(
    db: Session, schedule_id: Union[UUID, str]
) -> Optional[Stream]:
    stmt = select(Stream).where(Stream.schedule_id == schedule_id)
    return db.execute(stmt).scalar_one_or_none()


def update_stream(db: Session, stream_asset: Stream, **kwargs) -> Stream:
    for key, value in kwargs.items():
        if hasattr(stream_asset, key):
            setattr(stream_asset, key, value)

    stream_asset.updated_at = datetime.now()
    db.commit()
    db.refresh(stream_asset)

    return stream_asset


def delete_stream(db: Session, stream_asset: Stream) -> None:
    db.delete(stream_asset)
    db.commit()
