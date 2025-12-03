from datetime import datetime
from typing import Literal, Optional
from pytz import timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.Volunteer import Volunteer
from models.User import User


def get_all_volunteers(
    db: Session, search: Optional[str] = None, order_dir: Literal["asc", "desc"] = "asc"
) -> list[Volunteer]:
    # Query dasar
    stmt = select(Volunteer)

    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.join(User, Volunteer.user).where(
            (User.username.ilike(search_pattern))
            | (User.first_name.ilike(search_pattern))
            | (User.last_name.ilike(search_pattern))
            | (User.email.ilike(search_pattern))
        )

    # Atur order berdasarkan updated_at
    if order_dir == "asc":
        stmt = stmt.order_by(Volunteer.updated_at.asc())
    else:
        stmt = stmt.order_by(Volunteer.updated_at.desc())

    # Eksekusi query dan ambil hasilnya
    results = db.scalars(stmt).all()

    return results


def get_volunteer_by_id(db: Session, id: str) -> Optional[Volunteer]:
    stmt = select(Volunteer).where(Volunteer.id == id)
    return db.execute(stmt).scalar()


def get_volunteer_by_user_id(
    db: Session, user_id: str, exclude_user_id: Optional[str] = None
) -> Optional[Volunteer]:
    stmt = select(Volunteer).where(Volunteer.user_id == user_id)
    if exclude_user_id:
        stmt = stmt.where(Volunteer.user_id != exclude_user_id)
    return db.execute(stmt).scalar()


def create_volunteer(
    db: Session,
    user: User,
    now: Optional[datetime] = None,
    is_commit: bool = True,
) -> Volunteer:
    if now is None:
        now = datetime.now().astimezone(timezone("Asia/Jakarta"))
    new_volunteer = Volunteer(
        user=user,
        created_at=now,
        updated_at=now,
    )
    db.add(new_volunteer)
    if is_commit:
        db.commit()
    return new_volunteer


def update_volunteer(
    db: Session,
    volunteer: Volunteer,
    user: User,
    now: Optional[datetime] = None,
    is_commit: bool = True,
) -> Volunteer:
    if now is None:
        now = datetime.now().astimezone(timezone("Asia/Jakarta"))
    volunteer.user = user
    volunteer.updated_at = now
    if is_commit:
        db.commit()
    return volunteer


def delete_volunteer(
    db: Session,
    volunteer: Volunteer,
    is_commit: bool = True,
) -> None:
    db.delete(volunteer)
    if is_commit:
        db.commit()
