from datetime import datetime, timedelta
from typing import Optional, Tuple

import bcrypt
import jwt
import pytz
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pytz import timezone
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session as SQLAlchemySession

from models import get_db_sync
from models.RefreshToken import RefreshToken
from models.Token import Token
from models.User import User
from schemas.auth import AuthorizationStatusEnum
from settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    TZ,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token/", auto_error=False)


def generate_hash_password(password: str) -> str:
    hash = bcrypt.hashpw(str.encode(password), bcrypt.gensalt())
    return hash.decode()


def validated_password(hash: str, password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hash.encode())
    except Exception:
        return False


async def generate_token_from_user(
    db: SQLAlchemySession, user: User, ignore_timezone: bool = False
) -> Tuple[str, str]:
    expire = datetime.now() + timedelta(minutes=float(ACCESS_TOKEN_EXPIRE_MINUTES))
    if ignore_timezone is False:  # For testing
        expire = expire.astimezone(timezone(TZ))
    """
    {
        "user_id": "aaaa-bbbb-cccc-dddd",
        "username": "someusername",
        "exp": 1641455971,
    }
    """
    payload = {
        "id": str(user.id),
        "username": user.username,
        "exp": expire,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    new_token = Token(user=user, token=token, expired_at=expire)
    db.add(new_token)
    refresh_expire = datetime.now() + timedelta(
        minutes=float(REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "id": str(user.id),
        "username": user.username,
        "exp": expire,
    }
    refresh_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    new_refresh_token = RefreshToken(
        user=user,
        refresh_token=refresh_token,
        token=new_token,
        expired_at=refresh_expire,
    )
    db.add(new_refresh_token)
    db.commit()
    return (token, refresh_token)


def get_user_from_token(db: SQLAlchemySession, token: str) -> Optional[User]:
    now = datetime.now().astimezone(pytz.timezone(TZ))
    try:
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        id = payload.get("id")
    except Exception:
        invalidate_token(db=db, token=token)
        return None

    stmt = select(Token).where(Token.token == token, Token.user_id == id)
    session = db.execute(stmt).scalar()
    if session is None:
        return None
    if session.expired_at <= now:
        invalidate_token(db=db, token=token)
        return None

    return session.user


def get_current_user(
    db: Session = Depends(get_db_sync), token: str = Depends(oauth2_scheme)
) -> Optional[User]:
    return get_user_from_token(db, token)


def invalidate_token(db: SQLAlchemySession, token: str):
    # clear all expired token and selected_token
    now = datetime.now().astimezone(pytz.timezone(TZ))
    stmt = delete(Token).where(or_(Token.expired_at <= now, Token.token == token))
    db.execute(stmt)
    db.commit()


def check_permissions(
    current_user: User | None, required_participant_type: str
) -> AuthorizationStatusEnum:
    """Check if the current user has the required permissions.
    Args:
        current_user (User | None): The current authenticated user.
        required_participant_type (str): The required participant type for access.
    Returns:
        AuthorizationStatusEnum: The authorization status.
    """
    if current_user is None:
        return AuthorizationStatusEnum.UNAUTHORIZED
    if current_user.participant_type != required_participant_type:
        return AuthorizationStatusEnum.FORBIDDEN
    return AuthorizationStatusEnum.PASSED
