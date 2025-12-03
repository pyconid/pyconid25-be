import datetime
import uuid
from models import Base
from sqlalchemy import UUID, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship


class Volunteer(Base):
    __tablename__ = "volunteer"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(
        "user_id", ForeignKey("user.id"), nullable=False
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

    # Relationships
    user = relationship("User", back_populates="volunteer", foreign_keys=[user_id])
