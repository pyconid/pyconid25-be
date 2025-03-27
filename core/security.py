from typing import Optional, Tuple
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
import bcrypt
from pytz import timezone
import pytz
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session as SQLAlchemySession
from models.RefreshToken import RefreshToken
from models.Token import Token
import jwt
from models.User import User
from settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM,
    TZ,
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token/")


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


def invalidate_token(db: SQLAlchemySession, token: str):
    # clear all expired token and selected_token
    now = datetime.now().astimezone(pytz.timezone(TZ))
    stmt = delete(Token).where(or_(Token.expired_at <= now, Token.token == token))
    db.execute(stmt)
    db.commit()
