from typing import Optional, List
from pytz import timezone
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from models.Payment import Payment, PaymentStatus
from settings import TZ


def create_payment(
    db: Session,
    user_id: str,
    amount: int,
    ticket_id: str,
    payment_link: Optional[str] = None,
    description: Optional[str] = None,
    status: PaymentStatus = PaymentStatus.UNPAID,
    mayar_id: Optional[str] = None,
    mayar_transaction_id: Optional[str] = None,
    voucher_id: Optional[str] = None,
    is_commit: bool = True,
) -> Payment:
    now = datetime.now(timezone(TZ))

    payment = Payment(
        user_id=user_id,
        ticket_id=ticket_id,
        payment_link=payment_link,
        amount=amount,
        description=description,
        status=status,
        mayar_id=mayar_id,
        mayar_transaction_id=mayar_transaction_id,
        voucher_id=voucher_id,
        created_at=now,
        paid_at=None,
    )
    db.add(payment)
    db.flush()
    if is_commit:
        db.commit()
        db.refresh(payment)
    return payment


def get_payment_by_id(db: Session, payment_id: str) -> Optional[Payment]:
    stmt = select(Payment).where(Payment.id == payment_id)
    payment = db.execute(stmt).scalar()
    return payment


def get_payments_by_user_id(
    db: Session,
    user_id: str,
    status: Optional[PaymentStatus] = None,
    exclude_payment_id: Optional[str] = None,
) -> List[Payment]:
    stmt = (
        select(Payment)
        .options(joinedload(Payment.ticket))
        .where(Payment.user_id == user_id)
        .order_by(Payment.created_at.desc())
    )
    if exclude_payment_id:
        stmt = stmt.where(Payment.id != exclude_payment_id)
    if status is not None:
        stmt = stmt.where(
            Payment.status == status.value
            if isinstance(status, PaymentStatus)
            else status
        )
    payments = db.execute(stmt).scalars().all()
    return list(payments)


def update_payment(
    db: Session,
    payment: Payment,
    status: Optional[PaymentStatus] = None,
    payment_link: Optional[str] = None,
    mayar_id: Optional[str] = None,
    mayar_transaction_id: Optional[str] = None,
    is_commit: bool = True,
) -> Payment:
    if status is not None:
        payment.status = status.value if isinstance(status, PaymentStatus) else status
        if status == PaymentStatus.PAID and payment.paid_at is None:
            payment.paid_at = datetime.now(timezone(TZ))
        elif status == PaymentStatus.CLOSED and payment.closed_at is None:
            payment.closed_at = datetime.now(timezone(TZ))
    if mayar_id is not None:
        payment.mayar_id = mayar_id
    if mayar_transaction_id is not None:
        payment.mayar_transaction_id = mayar_transaction_id
    if payment_link is not None:
        payment.payment_link = payment_link

    if is_commit:
        db.commit()
        db.refresh(payment)

    return payment


def get_payment_by_mayar_id(db: Session, mayar_id: str) -> Optional[Payment]:
    stmt = select(Payment).where(Payment.mayar_id == mayar_id)
    payment = db.execute(stmt).scalar()
    return payment


def get_payment_by_mayar_transaction_id(
    db: Session, mayar_transaction_id: str
) -> Optional[Payment]:
    stmt = select(Payment).where(Payment.mayar_transaction_id == mayar_transaction_id)
    payment = db.execute(stmt).scalar()
    return payment


def get_user_paid_payment(
    db: Session,
    user_id: str,
) -> Optional[Payment]:
    stmt = (
        select(Payment)
        .options(joinedload(Payment.ticket), joinedload(Payment.voucher))
        .where(
            Payment.user_id == user_id,
            Payment.status == PaymentStatus.PAID.value,
        )
    )
    payment = db.execute(stmt).scalar()
    return payment


def close_other_unpaid_payments(
    db: Session,
    user_id: str,
    exclude_payment_id: Optional[str] = None,
    is_commit: bool = True,
) -> int:
    stmt = select(Payment).where(
        Payment.user_id == user_id,
        Payment.status == PaymentStatus.UNPAID.value,
    )

    if exclude_payment_id:
        stmt = stmt.where(Payment.id != exclude_payment_id)

    payments_to_close = db.execute(stmt).scalars().all()

    now = datetime.now(timezone(TZ))
    count = 0
    for payment in payments_to_close:
        payment.status = PaymentStatus.CLOSED.value
        payment.closed_at = now
        count += 1

    if is_commit and count > 0:
        db.commit()

    return count
