import uuid
from models import Base
from sqlalchemy import UUID, DateTime, ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped, relationship


class Token(Base):
    __tablename__ = "token"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(
        "user_id", ForeignKey("user.id"), index=True, nullable=False
    )
    token: Mapped[str] = mapped_column("token", String, nullable=False)
    expired_at = mapped_column("expired_at", DateTime(timezone=True), nullable=False)

    # Many to One
    user = relationship("User", back_populates="tokens", foreign_keys=[user_id])
