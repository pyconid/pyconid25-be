import uuid
from datetime import datetime

from models import Base
from sqlalchemy import UUID, Boolean, DateTime, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum


class StreamStatus(enum.StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    STREAMING = "STREAMING"
    ENDED = "ENDED"
    FAILED = "FAILED"


class StreamAsset(Base):
    __tablename__ = "stream_asset"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    schedule_id: Mapped[str] = mapped_column(
        "schedule_id",
        UUID(as_uuid=True),
        ForeignKey("schedule.id"),
        nullable=True,
        index=True,
    )
    mux_asset_id: Mapped[str] = mapped_column(
        "mux_asset_id", String(255), nullable=True, index=True
    )
    mux_playback_id: Mapped[str] = mapped_column(
        "mux_playback_id", String(255), nullable=True, index=True
    )
    mux_signed_playback_id: Mapped[str] = mapped_column(
        "mux_signed_playback_id", String(255), nullable=True, index=True
    )
    mux_live_stream_id: Mapped[str] = mapped_column(
        "mux_live_stream_id", String(255), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column("title", String(255), nullable=False)
    description: Mapped[str] = mapped_column("description", Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(
        "is_public", Boolean, nullable=False, default=True, index=True
    )
    is_live: Mapped[bool] = mapped_column(
        "is_live", Boolean, nullable=False, default=False, index=True
    )

    status: Mapped[StreamStatus] = mapped_column(
        "status",
        Enum(StreamStatus),
        nullable=False,
        default=StreamStatus.PENDING,
        index=True,
    )

    duration: Mapped[int] = mapped_column(
        "duration", Integer, nullable=True, comment="Duration in seconds"
    )
    thumbnail_url: Mapped[str] = mapped_column(
        "thumbnail_url", String(500), nullable=True
    )

    view_count: Mapped[int] = mapped_column(
        "view_count", Integer, nullable=False, default=0
    )
    max_concurrent_viewers: Mapped[int] = mapped_column(
        "max_concurrent_viewers", Integer, nullable=False, default=0
    )

    stream_started_at: Mapped[datetime] = mapped_column(
        "stream_started_at", DateTime(timezone=True), nullable=True
    )
    stream_ended_at: Mapped[datetime] = mapped_column(
        "stream_ended_at", DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    deleted_at: Mapped[datetime] = mapped_column(
        "deleted_at", DateTime(timezone=True), nullable=True
    )

    schedule = relationship(
        "Schedule", back_populates="stream_asset", foreign_keys=[schedule_id]
    )
    stream_views = relationship(
        "StreamView", back_populates="stream_asset", cascade="all, delete-orphan"
    )
