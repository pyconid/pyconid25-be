import datetime
import uuid
from models import Base
from sqlalchemy import UUID, DateTime, ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped, relationship

from models.Speaker import Speaker
from models.StreamAsset import StreamAsset


class Schedule(Base):
    __tablename__ = "schedule"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    topic: Mapped[str] = mapped_column("topic", String)
    speaker_id: Mapped[str] = mapped_column(
        "speaker_id", UUID(as_uuid=True), ForeignKey("speaker.id"), index=True
    )
    description: Mapped[str] = mapped_column("description", String, nullable=True)

    stream_link: Mapped[str] = mapped_column("stream_link", String, nullable=True)

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
    speaker: Mapped[Speaker] = relationship("Speaker", backref="schedules")
    stream_asset: Mapped[StreamAsset] = relationship(
        "StreamAsset", back_populates="schedule", uselist=False
    )
