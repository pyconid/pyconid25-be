import datetime
import uuid
from models import Base
from sqlalchemy import UUID, Boolean, DateTime, String
from sqlalchemy.orm import mapped_column, Mapped


class Speaker(Base):
    __tablename__ = "speaker"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column("name", String)
    bio: Mapped[str] = mapped_column("bio", String, nullable=True)
    photo_url: Mapped[str] = mapped_column("photo_url", String, nullable=True)
    email: Mapped[str] = mapped_column("email", String, nullable=True)
    instagram_link: Mapped[str] = mapped_column("instagram_link", String, nullable=True)
    x_link: Mapped[str] = mapped_column("x_link", String, nullable=True)

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

    is_keynote_speaker: Mapped[bool] = mapped_column(
        "is_keynote_speaker", Boolean, default=False
    )
