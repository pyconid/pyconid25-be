import uuid
from sqlalchemy import UUID, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column, Mapped
from models import Base


class Voucher(Base):
    __tablename__ = "voucher"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column("code", String, unique=True, nullable=False)
    value: Mapped[int] = mapped_column("value", Integer, default=0)
    type: Mapped[str] = mapped_column("type", String, nullable=True)
    email_whitelist: Mapped[dict] = mapped_column(
        "email_whitelist", JSONB, nullable=True
    )
    quota: Mapped[int] = mapped_column("quota", Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column("is_active", Boolean, default=False)
