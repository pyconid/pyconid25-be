from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.responses import (
    common_response,
    Ok,
    BadRequest,
    Unauthorized,
)
from core.security import (
    generate_token_from_user,
    get_user_from_token,
    invalidate_token,
    validated_password,
    oauth2_scheme,
)
from models import get_db_sync
from schemas.common import (
    BadRequestResponse,
    InternalServerErrorResponse,
    UnauthorizedResponse,
)
from schemas.auth import (
    LoginSuccessResponse,
    LoginRequest,
    MeResponse,
)
from repository import user as userRepo

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login/",
    responses={
        "200": {"model": LoginSuccessResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def login(request: LoginRequest, db: Session = Depends(get_db_sync)):
    user = userRepo.get_user_by_username(db=db, username=request.username)
    if user is None:
        return common_response(BadRequest(message="Invalid Credentials"))

    if not user.is_active:
        return common_response(BadRequest(message="Invalid Credentials"))

    is_valid = validated_password(user.password, request.password)
    if not is_valid:
        return common_response(BadRequest(message="Invalid Credentials"))

    (token, refresh_token) = await generate_token_from_user(db=db, user=user)
    return common_response(
        Ok(
            data={
                "id": str(user.id),
                "username": user.username,
                "is_active": user.is_active,
                "token": token,
                "refresh_token": refresh_token,
            }
        )
    )


@router.get(
    "/me/",
    responses={
        "200": {"model": MeResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def me(db: Session = Depends(get_db_sync), token: str = Depends(oauth2_scheme)):
    user = get_user_from_token(db=db, token=token)
    if user is None:
        return common_response(Unauthorized(message="Invalid Credentials"))

    return common_response(Ok(data={"id": str(user.id), "username": user.username}))


@router.post(
    "/logout/",
    responses={
        "200": {"model": LoginSuccessResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def logout(
    db: Session = Depends(get_db_sync), token: str = Depends(oauth2_scheme)
):
    user = get_user_from_token(db=db, token=token)
    if user is None:
        return common_response(Unauthorized(message="Invalid Credentials"))

    invalidate_token(db=db, token=token)
    return common_response(Ok(data={"message": "logout successfully"}))
