from datetime import datetime, timedelta
import traceback
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pytz import timezone
from sqlalchemy.orm import Session
from core.email import send_email_verfication, send_reset_password_email
from core.oauth import github_service, google_service
from core.responses import (
    InternalServerError,
    NoContent,
    common_response,
    Ok,
    BadRequest,
    Unauthorized,
    handle_http_exception,
)
from core.security import (
    generate_hash_password,
    generate_token_from_user,
    get_user_from_token,
    invalidate_token,
    validated_password,
    oauth2_scheme,
)
from models import get_db_sync
from models.User import User
from schemas.common import (
    BadRequestResponse,
    InternalServerErrorResponse,
    NoContentResponse,
    UnauthorizedResponse,
)
from schemas.auth import (
    EmailVerifiedSuccessResponse,
    ForgotPasswordRequest,
    ForgotPasswordSuccessResponse,
    GoogleSignInResponse,
    GoogleVerifiedResponse,
    LoginEmailRequest,
    LoginSuccessResponse,
    MeResponse,
    GithubVerifiedResponse,
    GithubSignInResponse,
    OauthSignInRequest,
    ResetPasswordRequest,
    ResetPasswordSuccessResponse,
    SignUpRequest,
)
from repository import user as userRepo
from repository import email_verification as emailVerificationRepo
from repository import reset_password as resetPasswordRepo
from settings import FRONTEND_BASE_URL, TZ

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token/")
async def swagger_form_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db_sync)
):
    user = userRepo.get_user_by_username(db=db, username=form_data.username)
    if user is None:
        return common_response(BadRequest(message="Invalid Credentials"))

    if not user.is_active:
        return common_response(BadRequest(message="Invalid Credentials"))

    is_valid = validated_password(user.password, form_data.password)
    if not is_valid:
        return common_response(BadRequest(message="Invalid Credentials"))

    (token, refresh_token) = await generate_token_from_user(db=db, user=user)

    return {"access_token": token, "token_type": "bearer"}


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

    return common_response(
        Ok(
            data={
                "id": str(user.id),
                "username": user.username,
                "participant_type": user.participant_type,
            }
        )
    )


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


@router.post(
    "/email/signup/",
    responses={
        "204": {"model": NoContentResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def email_signup(request: SignUpRequest, db: Session = Depends(get_db_sync)):
    existing_user = userRepo.get_user_by_email(db=db, email=request.email)
    if existing_user:
        return common_response(BadRequest(message="Email already registered"))

    verification_code = emailVerificationRepo.generate_verification_code()
    expired_at = datetime.now().astimezone(timezone(TZ)) + timedelta(hours=12)
    existing_verification = emailVerificationRepo.get_email_verification_by_email(
        db=db, email=request.email
    )
    if existing_verification:
        emailVerificationRepo.update_email_verification(
            db=db,
            email_verification=existing_verification,
            email=request.email,
            username=request.username,
            password=generate_hash_password(request.password),
            verification_code=verification_code,
            expired_at=expired_at,
            is_commit=False,
        )
    else:
        emailVerificationRepo.create_email_verification(
            db=db,
            email=request.email,
            username=request.username,
            password=generate_hash_password(request.password),
            verification_code=verification_code,
            expired_at=expired_at,
            is_commit=False,
        )
    activation_link = (
        f"{FRONTEND_BASE_URL}/email-verification/?token={verification_code}"
    )
    await send_email_verfication(
        recipient=request.email, activation_link=activation_link
    )
    db.commit()
    return common_response(NoContent())


@router.get(
    "/email/verified/",
    responses={
        "200": {"model": EmailVerifiedSuccessResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def email_verified(
    token: str = None,
    db: Session = Depends(get_db_sync),
):
    if not token:
        return common_response(BadRequest(message="Token tidak ditemukan"))

    email_verification = (
        emailVerificationRepo.get_email_verification_by_verfication_code(
            db=db, verification_code=token
        )
    )
    if not email_verification:
        return common_response(BadRequest(message="token tidak valid"))

    if email_verification.expired_at < datetime.now().astimezone(timezone(TZ)):
        emailVerificationRepo.delete_email_verification(
            db=db, email_verification=email_verification
        )
        return common_response(BadRequest(message="Token expired, mohon daftar ulang"))

    existing_user = userRepo.get_user_by_email(db=db, email=email_verification.email)
    if existing_user:
        return common_response(BadRequest(message="Email sudah terdaftar"))

    now = datetime.now().astimezone(timezone(TZ))
    userRepo.create_user(
        db=db,
        username=email_verification.username,
        password=email_verification.password,
        email=email_verification.email,
        is_active=True,
        created_at=now,
        updated_at=now,
        deleted_at=None,
        is_commit=False,
    )
    emailVerificationRepo.delete_email_verification(
        db=db, email_verification=email_verification, is_commit=False
    )
    db.commit()
    return common_response(Ok(data={"message": "Email verified successfully"}))


@router.post(
    "/email/signin/",
    responses={
        "200": {"model": LoginSuccessResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def email_signin(request: LoginEmailRequest, db: Session = Depends(get_db_sync)):
    user = userRepo.get_user_by_email(db=db, email=request.email)
    if user is None:
        return common_response(BadRequest(message="Invalid Credentials"))

    if user.password is None:
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


@router.post(
    "/email/forgot-password/",
    responses={
        "200": {"model": ForgotPasswordSuccessResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def forgot_password(
    request: ForgotPasswordRequest, db: Session = Depends(get_db_sync)
):
    user = userRepo.get_user_by_email(db=db, email=request.email)
    if user is None:
        return common_response(BadRequest(message="email tidak terdaftar"))

    token = resetPasswordRepo.generate_token()
    expired_at = datetime.now().astimezone(timezone(TZ)) + timedelta(hours=12)
    existing_reset_password = resetPasswordRepo.get_reset_password_by_user(
        db=db, user=user
    )
    if existing_reset_password:
        resetPasswordRepo.update_reset_password(
            db=db,
            reset_password=existing_reset_password,
            user=user,
            token=token,
            expired_at=expired_at,
            is_commit=False,
        )
    else:
        existing_reset_password = resetPasswordRepo.create_reset_password(
            db=db,
            user=user,
            token=token,
            expired_at=expired_at,
            is_commit=False,
        )
    reset_link = f"{FRONTEND_BASE_URL}/reset-password/?token={token}"
    await send_reset_password_email(recipient=request.email, reset_link=reset_link)
    db.commit()
    return common_response(Ok(data={"message": "silahkan cek email anda"}))


@router.post(
    "/email/reset-password/",
    responses={
        "200": {"model": ResetPasswordSuccessResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def reset_password(
    request: ResetPasswordRequest, db: Session = Depends(get_db_sync)
):
    reset_password = resetPasswordRepo.get_reset_password_by_token(
        db=db, token=request.token
    )
    if not reset_password:
        return common_response(BadRequest(message="token tidak valid"))

    if reset_password.expired_at < datetime.now().astimezone(timezone(TZ)):
        resetPasswordRepo.delete_reset_password(db=db, reset_password=reset_password)
        return common_response(BadRequest(message="Token expired"))

    user: User = reset_password.user
    if not user:
        return common_response(BadRequest(message="User tidak ditemukan"))

    user.password = generate_hash_password(request.new_password)
    user.updated_at = datetime.now().astimezone(timezone(TZ))
    db.add(user)

    resetPasswordRepo.delete_reset_password(
        db=db, reset_password=reset_password, is_commit=False
    )
    db.commit()
    return common_response(Ok(data={"message": "Password berhasil diubah"}))


@router.post(
    "/github/signin/",
    responses={
        "200": {"model": GithubSignInResponse},
        "307": {
            "description": "Redirect to oauth provider",
            "content": {"text/html": {"example": "Redirecting..."}},
        },
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def github_signin(http_request: Request, params: OauthSignInRequest = Depends()):
    try:
        authorization_url = await github_service.initiate_oauth(
            request=http_request,
            follow_redirect=params.follow_redirect,
        )

        if isinstance(authorization_url, RedirectResponse):
            return authorization_url
        return common_response(Ok(data={"redirect": authorization_url}))
    except HTTPException as e:
        return handle_http_exception(e)
    except Exception as e:
        traceback.print_exc()
        return common_response(
            InternalServerError(error=f"Failed to initiate OAuth github: {str(e)}")
        )


@router.post(
    "/github/verified/",
    responses={
        "200": {"model": GithubVerifiedResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def github_verified(
    http_request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db_sync),
):
    try:
        if not code:
            return common_response(BadRequest(message="Code not found"))

        oauth_result = await github_service.handle_verified(request=http_request, db=db)

        user = oauth_result["user"]
        is_new_user = oauth_result["is_new_user"]
        provider_user_info = oauth_result["provider_user_info"]

        token, refresh_token = await generate_token_from_user(db=db, user=user)

        response = {
            "token": token,
            "refresh_token": refresh_token,
            "id": str(user.id),
            "username": user.username,
            "is_new_user": is_new_user,
            "github_username": provider_user_info.get("username"),
        }

        return common_response(Ok(data=response))
    except HTTPException as e:
        return handle_http_exception(e)
    except Exception as e:
        traceback.print_exc()
        return common_response(
            InternalServerError(
                error=f"Failed to handle OAuth verified github: {str(e)}"
            )
        )


@router.post(
    "/google/signin/",
    responses={
        "200": {"model": GoogleSignInResponse},
        "307": {
            "description": "Redirect to oauth provider",
            "content": {"text/html": {"example": "Redirecting..."}},
        },
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def google_signin(http_request: Request, params: OauthSignInRequest = Depends()):
    try:
        authorization_url = await google_service.initiate_oauth(
            request=http_request,
            follow_redirect=params.follow_redirect,
        )

        if isinstance(authorization_url, RedirectResponse):
            return authorization_url
        return common_response(Ok(data={"redirect": authorization_url}))
    except HTTPException as e:
        return handle_http_exception(e)
    except Exception as e:
        traceback.print_exc()
        return common_response(
            InternalServerError(error=f"Failed to initiate OAuth google: {str(e)}")
        )


@router.post(
    "/google/verified/",
    responses={
        "200": {"model": GoogleVerifiedResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def google_verified(
    http_request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db_sync),
):
    try:
        if not code:
            return common_response(BadRequest(message="Code not found"))

        oauth_result = await google_service.handle_verified(request=http_request, db=db)

        user = oauth_result["user"]
        is_new_user = oauth_result["is_new_user"]
        provider_user_info = oauth_result["provider_user_info"]

        token, refresh_token = await generate_token_from_user(db=db, user=user)

        response = {
            "token": token,
            "refresh_token": refresh_token,
            "id": str(user.id),
            "username": user.username,
            "is_new_user": is_new_user,
            "google_email": provider_user_info.get("email"),
        }

        return common_response(Ok(data=response))
    except HTTPException as e:
        return handle_http_exception(e)
    except Exception as e:
        traceback.print_exc()
        return common_response(
            InternalServerError(
                error=f"Failed to handle OAuth verified google: {str(e)}"
            )
        )
