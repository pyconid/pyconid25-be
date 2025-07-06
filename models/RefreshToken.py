import uuid
from models import Base
from sqlalchemy import UUID, DateTime, ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped, relationship


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(
        "user_id", ForeignKey("user.id"), index=True, nullable=False
    )
    refresh_token: Mapped[str] = mapped_column("refresh_token", String, nullable=False)
    expired_at = mapped_column("expired_at", DateTime(timezone=True), nullable=False)
    token_id: Mapped[str] = mapped_column(
        "token_id", ForeignKey("token.id", ondelete="CASCADE"), nullable=False
    )

    # Many to One
    user = relationship("User", back_populates="refresh_tokens", foreign_keys=[user_id])
    token = relationship(
        "Token", backref="refresh_token_token", foreign_keys=[token_id]
    )
