import datetime
import uuid
from typing import List

from sqlalchemy import UUID, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base


class Schedule(Base):
    __tablename__ = "schedule"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    speaker_id: Mapped[str] = mapped_column(
        "speaker_id",
        UUID(as_uuid=True),
        ForeignKey("speaker.id"),
        index=True,
        nullable=True,
    )
    room_id: Mapped[str] = mapped_column(
        "room_id", UUID(as_uuid=True), ForeignKey("room.id"), index=True, nullable=True
    )
    schedule_type_id: Mapped[str] = mapped_column(
        "schedule_type_id",
        UUID(as_uuid=True),
        ForeignKey("schedule_type.id"),
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column("title", String)
    description: Mapped[str] = mapped_column("description", String, nullable=True)

    # Presentation and Slide fields
    presentation_language: Mapped[str] = mapped_column(
        "presentation_language", String, nullable=True
    )
    slide_language: Mapped[str] = mapped_column("slide_language", String, nullable=True)
    slide_link: Mapped[str] = mapped_column("slide_link", String, nullable=True)
    tags: Mapped[List[str]] = mapped_column("tags", ARRAY(String), nullable=True)

    start = mapped_column("start", DateTime(timezone=True), nullable=True)
    end = mapped_column("end", DateTime(timezone=True), nullable=True)

    created_at = mapped_column(
        "created_at",
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.timezone.utc),
    )
    updated_at = mapped_column(
        "updated_at",
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.timezone.utc),
    )
    deleted_at = mapped_column("deleted_at", DateTime(timezone=True))

    # Relationships
    speaker = relationship("Speaker", backref="schedules")
    room = relationship("Room", back_populates="schedules")
    schedule_type = relationship("ScheduleType", back_populates="schedules")
    stream = relationship(
        "Stream", back_populates="schedule", uselist=False, cascade="all, delete-orphan"
    )
