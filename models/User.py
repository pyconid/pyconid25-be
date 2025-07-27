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
    password: Mapped[str] = mapped_column("password", String, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        "is_active", Boolean, nullable=True, default=False
    )
    github_id: Mapped[str] = mapped_column(
        "github_id", String(255), nullable=True, index=True
    )
    github_username: Mapped[str] = mapped_column(
        "github_username", String(255), nullable=True
    )
    created_at = mapped_column("created_at", DateTime(timezone=True))
    updated_at = mapped_column("updated_at", DateTime(timezone=True))
    deleted_at = mapped_column("deleted_at", DateTime(timezone=True))

    # One to Many
    tokens = relationship("Token", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
