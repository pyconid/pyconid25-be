import traceback
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from core.oauth import github_service, google_service
from core.responses import (
    InternalServerError,
    common_response,
    Ok,
    BadRequest,
    Unauthorized,
    handle_http_exception,
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
    GoogleSignInResponse,
    GoogleVerifiedResponse,
    LoginSuccessResponse,
    LoginRequest,
    MeResponse,
    GithubVerifiedResponse,
    GithubSignInResponse,
    OauthSignInRequest,
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
