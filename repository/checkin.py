from sqlalchemy import select
from sqlalchemy.orm import Session

from models.Payment import Payment
from models.User import User


def get_user_data_by_payment_id(db: Session, payment_id: str)-> User | None:
    """ Find user data based on Payment ID

    Args:
        db (Session): Database session
        payment_id (str): Payment ID

    Returns:
        User | None: User data or None if not found
    """
    query = (
        select(User)
        .join(Payment, Payment.user_id == User.id)
        .where(Payment.id == payment_id)
    )
    return db.execute(query).scalar_one_or_none()

