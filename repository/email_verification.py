from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.EmailVerification import EmailVerification
import random
import string


def generate_verification_code() -> str:
    length = 25
    characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
    verification_code = "".join(random.choice(characters) for _ in range(length))
    return verification_code


def get_email_verification_by_email(
    db: Session, email: str
) -> Optional[EmailVerification]:
    stmt = select(EmailVerification).where(EmailVerification.email == email)
    data = db.execute(stmt).scalar()
    return data


def get_email_verification_by_verfication_code(
    db: Session, verification_code: str
) -> Optional[EmailVerification]:
    stmt = select(EmailVerification).where(
        EmailVerification.verification_code == verification_code
    )
    data = db.execute(stmt).scalar()
    return data


def create_email_verification(
    db: Session,
    email: str,
    username: str,
    password: str,
    verification_code: str,
    expired_at: datetime,
    is_commit: bool = True,
) -> EmailVerification:
    new_verification = EmailVerification(
        email=email,
        username=username,
        password=password,
        verification_code=verification_code,
        expired_at=expired_at,
    )
    db.add(new_verification)
    if is_commit:
        db.commit()
    return new_verification


def update_email_verification(
    db: Session,
    email_verification: EmailVerification,
    email: str,
    username: str,
    password: str,
    verification_code: str,
    expired_at: datetime,
    is_commit: bool = True,
):
    email_verification.email = email
    email_verification.username = username
    email_verification.password = password
    email_verification.verification_code = verification_code
    email_verification.expired_at = expired_at
    db.add(email_verification)
    if is_commit:
        db.commit()


def delete_email_verification(
    db: Session,
    email_verification: EmailVerification,
    is_commit: bool = True,
):
    db.delete(email_verification)
    if is_commit:
        db.commit()
