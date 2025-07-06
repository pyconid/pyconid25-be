import uuid
from models import Base
from sqlalchemy import UUID, DateTime, String, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column("username", String, nullable=True)
    password: Mapped[str] = mapped_column("password", String, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        "is_active", Boolean, nullable=True, default=False
    )
    created_at = mapped_column("created_at", DateTime(timezone=True))
    updated_at = mapped_column("updated_at", DateTime(timezone=True))
    deleted_at = mapped_column("deleted_at", DateTime(timezone=True))

    # One to Many
    tokens = relationship("Token", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
