import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session
from core.log import logger

from models.Payment import Payment
from models.User import User
from schemas.checkin import CheckinDayEnum
from settings import TZ

def get_user_data_by_payment_id(db: Session, payment_id: str) -> User | None:
    """Find user data based on Payment ID

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


def get_user_and_payment_by_payment_id(
    db: Session, payment_id: str
) -> tuple[User, Payment] | None:
    """Find user and payment data by Payment ID

    Args:
        db (Session): Database session
        payment_id (str): Payment ID

    Returns:
        tuple[User, Payment] | None: Tuple of (User, Payment) or None if not found
    """
    query = (
        select(User, Payment)
        .join(Payment, Payment.user_id == User.id)
        .where(Payment.id == payment_id)
    )
    result = db.execute(query).first()
    if not result:
        return None
    user, payment = result
    return (user, payment)


def set_user_checkin_status(
    db: Session, user_id: str, day: CheckinDayEnum, status: bool, updated_by: str
) -> User | None:
    """Set user check-in status for a specific day

    Args:
        db (Session): Database session
        user_id (str): User ID
        day (CheckinDayEnum): Day for check-in (day1 or day2)
        status (bool): Check-in status to set

    Returns:
        User | None: Updated user or None if not found or error occurred
        
    """
    
    try:
        tz = ZoneInfo(TZ)
    except ZoneInfoNotFoundError:
        logger.error(f"Timezone {TZ} not found. Using UTC instead.")
        tz = ZoneInfo("UTC")
        
    try:
        user = db.get(User, user_id)

        if not user:
            return None
        now = datetime.datetime.now(tz)
        match day:
            case CheckinDayEnum.day1:
                user.attendance_day_1 = status
                user.attendance_day_1_updated_by = updated_by

                if status:
                    user.attendance_day_1_at = now
            case CheckinDayEnum.day2:
                user.attendance_day_2 = status
                user.attendance_day_2_updated_by = updated_by
                if status:
                    user.attendance_day_2_at = now

        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        logger.error(f"Error setting check-in status: {e}")
        db.rollback()
        return None

