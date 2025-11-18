import datetime
import uuid
from models import Base
from sqlalchemy import UUID, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship


class Speaker(Base):
    __tablename__ = "speaker"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(
        "user_id", ForeignKey("user.id"), nullable=False
    )
    speaker_type_id: Mapped[str] = mapped_column(
        "speaker_type_id", ForeignKey("speaker_type.id"), nullable=True
    )
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

    # is_keynote_speaker: Mapped[bool] = mapped_column(
    #     "is_keynote_speaker", Boolean, default=False
    # )

    # Relationships
    user = relationship("User", backref="speaker_user")
    speaker_type = relationship("SpeakerType", backref="speaker_speaker_type")
