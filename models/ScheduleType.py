import uuid
from models import Base
from sqlalchemy import UUID, DateTime, String
from sqlalchemy.orm import mapped_column, Mapped, relationship


class ScheduleType(Base):
    __tablename__ = "schedule_type"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)

    created_at = mapped_column("created_at", DateTime(timezone=True))
    updated_at = mapped_column("updated_at", DateTime(timezone=True))
    deleted_at = mapped_column("deleted_at", DateTime(timezone=True), nullable=True)

    # Relationships
    schedules = relationship("Schedule", back_populates="schedule_type")
