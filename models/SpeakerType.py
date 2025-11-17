import uuid
from sqlalchemy import UUID, String
from models import Base
from sqlalchemy.orm import mapped_column, Mapped


class SpeakerType(Base):
    __tablename__ = "speaker_type"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column("name", String)
