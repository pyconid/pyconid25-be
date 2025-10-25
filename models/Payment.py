from enum import StrEnum
import uuid
from models import Base
from sqlalchemy import UUID, DateTime, String, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship


class PaymentStatus(StrEnum):
    PAID = "paid"
    UNPAID = "unpaid"
    CLOSED = "closed"


class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(
        "user_id", UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    ticket_id: Mapped[str] = mapped_column(
        "ticket_id",
        UUID(as_uuid=True),
        ForeignKey("ticket.id"),
        nullable=False,
        index=True,
    )
    payment_link: Mapped[str] = mapped_column("payment_link", String, nullable=True)
    status: Mapped[str] = mapped_column(
        "status", String, nullable=False, default=PaymentStatus.UNPAID
    )
    created_at = mapped_column("created_at", DateTime(timezone=True), nullable=False)
    paid_at = mapped_column("paid_at", DateTime(timezone=True), nullable=True)
    closed_at = mapped_column("closed_at", DateTime(timezone=True), nullable=True)

    mayar_id: Mapped[str] = mapped_column("mayar_id", String, nullable=True, index=True)
    mayar_transaction_id: Mapped[str] = mapped_column(
        "mayar_transaction_id", String, nullable=True, index=True
    )
    amount: Mapped[int] = mapped_column("amount", nullable=False)
    description: Mapped[str] = mapped_column("description", String, nullable=True)

    # Relationship
    user = relationship("User", backref="payments_user")
    ticket = relationship("Ticket", backref="payments_ticket")
