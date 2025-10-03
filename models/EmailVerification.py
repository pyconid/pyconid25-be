from sqlalchemy import UUID, DateTime, String
from models import Base
from sqlalchemy.orm import mapped_column, Mapped
import uuid


class EmailVerification(Base):
    __tablename__ = "email_verification"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column("email", String, unique=True, index=True)
    username: Mapped[str] = mapped_column("username", String, nullable=False)
    password: Mapped[str] = mapped_column("password", String, nullable=False)
    verification_code: Mapped[str] = mapped_column("verification_code", String)
    expired_at = mapped_column("expired_at", DateTime(timezone=True), nullable=False)
