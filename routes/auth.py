import traceback
from typing import Optional
from urllib.parse import urlencode
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
    GitHubVerifiedRequest,
    GitHubVerifiedResponse,
    LoginSuccessResponse,
    LoginRequest,
    MeResponse,
    OAuthCallbackResponse,
    OAuthSignInResponse,
    OauthSignInRequest,
)
from repository import user as userRepo
from settings import FRONTEND_BASE_URL

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
        # session_data = dict(http_request.session)
        # print("=== OAuth Signin Debug ===")
        # print(f"Session data: {session_data}")
        # print(f"Session id: {http_request}")
        # print(f"All session keys: {list(session_data.keys())}")
        # print("==========================")
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
    except Exception:
        traceback.print_exc()
        return common_response(
            InternalServerError(error=f"Failed to login via {provider}")
        )


@router.get(
    "/{provider}/callback/",
    name="oauth_callback",
    responses={
        "200": {"model": OAuthCallbackResponse},
        "307": {
            "description": "Redirect to frontend",
            "content": {"text/html": {"example": "Redirecting..."}},
        },
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def oauth_callback(
    provider: str,
    http_request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db_sync),
):
    try:
        if error:
            error_url = f"{FRONTEND_BASE_URL}/auth/github/callback?error={error}"
            return RedirectResponse(url=error_url)

        if not code:
            error_url = f"{FRONTEND_BASE_URL}/auth/github/callback?error=missing_code"
            return RedirectResponse(url=error_url)

        # received_state = http_request.query_params.get("state")
        # session_data = dict(http_request.session)

        # print("=== OAuth Callback Debug ===")
        # print(f"State: {state}")
        # print(f"Received state: {received_state}")

        # matching_state_key = None
        # expected_state = None
        # print(session_data)

        # for key, value in session_data.items():
        #     print(f"Key: {key}, Value: {value}")
        #     if key.startswith(f"_state_{provider}_"):
        #         session_state = key.split("_")[-1]  # Extract state dari key
        #         print(f"Found session state in key: {key} -> state: {session_state}")

        #         if session_state == received_state:
        #             matching_state_key = key
        #             expected_state = session_state
        #             print("✅ State match found!")
        #             break
        #         else:
        #             print(f"❌ State mismatch: {session_state} != {received_state}")

        # print(f"Matching state key: {matching_state_key}")
        # print("==========================")

        oauth_result = await OAuthService.handle_callback(
            provider=provider, request=http_request, db=db
        )

        user = oauth_result["user"]
        account = oauth_result["account"]
        is_new_user = oauth_result["is_new_user"]

        token, refresh_token = await generate_token_from_user(db=db, user=user)

        params = {
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

        success_url = f"{FRONTEND_BASE_URL}/auth/github/callback?{urlencode(params)}"
        return RedirectResponse(url=success_url)
    except HTTPException as e:
        error_url = f"{FRONTEND_BASE_URL}/auth/github/callback?error={str(e.detail)}"
        return RedirectResponse(url=error_url)
    except Exception:
        traceback.print_exc()
        error_url = (
            f"{FRONTEND_BASE_URL}/auth/github/callback?error=authentication_failed"
        )
        return RedirectResponse(url=error_url)


@router.post(
    "/github/verified/",
    responses={
        "200": {"model": GitHubVerifiedResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def github_verified(
    request: GitHubVerifiedRequest, db: Session = Depends(get_db_sync)
):
    try:
        github_result = await OAuthService.verify_github_cookie(
            github_cookie=request.github_cookie, db=db
        )

        user = github_result["user"]
        account = github_result["account"]

        token, refresh_token = await generate_token_from_user(db=db, user=user)

        return common_response(
            Ok(
                data={
                    "id": str(user.id),
                    "github_username": account.provider_username,
                    "token": token,
                    "refresh_token": refresh_token,
                    "username": user.username,
                    "is_active": user.is_active,
                }
            )
        )
    except HTTPException as e:
        return handle_http_exception(e)
    except Exception:
        traceback.print_exc()
        return common_response(
            InternalServerError(error="Failed to verify github session")
        )
