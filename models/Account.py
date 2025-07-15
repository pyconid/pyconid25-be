import uuid
from models import Base
from sqlalchemy import UUID, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship


class Account(Base):
    __tablename__ = "account"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(
        "user_id", ForeignKey("user.id"), index=True, nullable=False
    )
    provider: Mapped[str] = mapped_column("provider", String(50), nullable=False)
    provider_id: Mapped[str] = mapped_column(
        "provider_id", String(255), nullable=False, index=True
    )
    provider_email: Mapped[str] = mapped_column(
        "provider_email", String(255), nullable=True
    )
    provider_username: Mapped[str] = mapped_column(
        "provider_username", String(255), nullable=True
    )
    provider_name: Mapped[str] = mapped_column(
        "provider_name", String(255), nullable=True
    )

    access_token: Mapped[str] = mapped_column("access_token", Text, nullable=True)
    refresh_token: Mapped[str] = mapped_column("refresh_token", Text, nullable=True)
    token_expires_at = mapped_column(
        "token_expires_at", DateTime(timezone=True), nullable=True
    )
    token_type: Mapped[str] = mapped_column("token_type", Text, nullable=True)
    scope: Mapped[str] = mapped_column("scope", Text, nullable=True)
    created_at = mapped_column("created_at", DateTime(timezone=True))
    updated_at = mapped_column("updated_at", DateTime(timezone=True))

    # Many to One
    user = relationship("User", back_populates="accounts", foreign_keys=[user_id])
