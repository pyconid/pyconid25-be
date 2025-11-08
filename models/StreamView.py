import uuid
from datetime import datetime

from models import Base
from sqlalchemy import UUID, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.StreamAsset import StreamAsset
from models.User import User


class StreamView(Base):
    __tablename__ = "stream_view"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    stream_asset_id: Mapped[str] = mapped_column(
        "stream_asset_id",
        UUID(as_uuid=True),
        ForeignKey("stream_asset.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        "started_at", DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[datetime] = mapped_column(
        "ended_at", DateTime(timezone=True), nullable=True
    )
    duration_watched: Mapped[int] = mapped_column(
        "duration_watched",
        Integer,
        nullable=False,
        default=0,
        comment="Duration watched in seconds",
    )

    ip_address: Mapped[str] = mapped_column("ip_address", String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column("user_agent", String(500), nullable=True)

    # Relationships
    stream_asset: Mapped[StreamAsset] = relationship(
        "StreamAsset", back_populates="stream_views"
    )
    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
