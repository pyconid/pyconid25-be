import uuid
from datetime import datetime

from models import Base
from sqlalchemy import UUID, Boolean, DateTime, String, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum


class StreamStatus(enum.StrEnum):
    PENDING = "PENDING"
    STREAMING = "STREAMING"
    ENDED = "ENDED"
    FAILED = "FAILED"


class Stream(Base):
    __tablename__ = "stream"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    schedule_id: Mapped[str] = mapped_column(
        "schedule_id",
        UUID(as_uuid=True),
        ForeignKey("schedule.id"),
        nullable=False,
        index=True,
    )
    mux_playback_id: Mapped[str] = mapped_column(
        "mux_playback_id", String(255), nullable=True, index=True
    )
    mux_live_stream_id: Mapped[str] = mapped_column(
        "mux_live_stream_id", String(255), nullable=True, index=True
    )

    is_public: Mapped[bool] = mapped_column(
        "is_public", Boolean, nullable=False, default=True, index=True
    )

    status: Mapped[str] = mapped_column(
        "status",
        String,
        nullable=False,
        default=StreamStatus.PENDING,
        index=True,
    )

    stream_started_at: Mapped[datetime] = mapped_column(
        "stream_started_at", DateTime(timezone=True), nullable=True
    )
    stream_ended_at: Mapped[datetime] = mapped_column(
        "stream_ended_at", DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime(timezone=True))

    # Relationship
    schedule = relationship(
        "Schedule", back_populates="stream", foreign_keys=[schedule_id]
    )
