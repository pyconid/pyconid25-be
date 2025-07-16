import traceback
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from core.oauth_service import OAuthService
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
    LoginSuccessResponse,
    LoginRequest,
    MeResponse,
    OAuthCallbackResponse,
    OAuthSignInResponse,
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
    "/{provider}/signin/",
    responses={
        "200": {"model": OAuthSignInResponse},
        "307": {
            "description": "Redirect to oauth provider",
            "content": {"text/html": {"example": "Redirecting..."}},
        },
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def oauth_signin(
    provider: str, http_request: Request, params: OauthSignInRequest = Depends()
):
    supported_providers = ["github"]
    if provider not in supported_providers:
        return common_response(BadRequest(message=f"Provider {provider} not supported"))

    try:
        authorization_url = await OAuthService.initiate_oauth(
            provider=provider,
            request=http_request,
            follow_redirect=params.follow_redirect,
        )

        if isinstance(authorization_url, RedirectResponse):
            return authorization_url
        return common_response(Ok(data={"redirect_url": authorization_url}))
    except HTTPException as e:
        return handle_http_exception(e)
    except Exception as e:
        traceback.print_exc()
        return common_response(
            InternalServerError(error=f"Failed to initiate OAuth {provider}: {str(e)}")
        )


@router.get(
    "/{provider}/verified/",
    responses={
        "200": {"model": OAuthCallbackResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def oauth_verified(
    provider: str,
    http_request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db_sync),
):
    try:
        if not code:
            return common_response(BadRequest(message="Code not found"))

        oauth_result = await OAuthService.handle_verified(
            provider=provider, request=http_request, db=db
        )

        user = oauth_result["user"]
        account = oauth_result["account"]
        is_new_user = oauth_result["is_new_user"]

        token, refresh_token = await generate_token_from_user(db=db, user=user)

        response = {
            "token": token,
            "refresh_token": refresh_token,
            "user_id": str(user.id),
            "username": user.username,
            "is_new_user": str(is_new_user).lower(),
            "provider": provider,
            "provider_username": account.provider_username,
            "provider_email": account.provider_email,
            "provider_name": account.provider_name,
        }

        return common_response(Ok(data=response))
    except HTTPException as e:
        return handle_http_exception(e)
    except Exception as e:
        traceback.print_exc()
        return common_response(
            InternalServerError(
                error=f"Failed to handle OAuth verified {provider}: {str(e)}"
            )
        )
