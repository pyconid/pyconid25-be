from datetime import datetime
import uuid
from sqlalchemy import UUID, DateTime, ForeignKey, String
from models import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship


class ResetPassword(Base):
    __tablename__ = "reset_password"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(
        "user_id", ForeignKey("user.id"), nullable=False
    )
    token: Mapped[str] = mapped_column("token", String, nullable=False)
    expired_at: Mapped[datetime] = mapped_column(
        "expired_at", DateTime(timezone=True), nullable=False
    )

    # relationships
    user = relationship("User", backref="reset_password_user", foreign_keys=[user_id])
