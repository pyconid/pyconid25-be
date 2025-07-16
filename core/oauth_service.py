from datetime import datetime, timedelta
import traceback
from typing import Optional, Tuple, TypedDict, Union
from fastapi import HTTPException, Request

from fastapi.responses import RedirectResponse
import pytz
from sqlalchemy import select
from sqlalchemy.orm import Session
from core.oauth_config import oauth_config
from core.security import generate_hash_password
from models.Account import Account
from models.User import User
from settings import FRONTEND_BASE_URL, TZ


class UserInfoResponse(TypedDict):
    id: str
    username: str
    email: Optional[str]
    name: Optional[str]
    provider: str


class HandleOauthResponse(TypedDict):
    user: User
    account: Account
    is_new_user: bool
    provider_user_info: UserInfoResponse


class VerifyOauthSessionResponse(TypedDict):
    user: User
    account: Account


class OAuthTokenResponse(TypedDict, total=False):
    access_token: str
    refresh_token: Optional[str]
    expires_in: Optional[int]
    token_type: Optional[str]
    scope: Optional[str]


class OAuthService:
    @staticmethod
    async def initiate_oauth(
        provider: str, request: Request, follow_redirect: Optional[bool] = False
    ) -> Union[RedirectResponse, str]:
        client = oauth_config.get_client(provider=provider)
        if not client:
            raise HTTPException(
                status_code=400, detail=f"Provider {provider} not supported"
            )

        if FRONTEND_BASE_URL is None:
            raise HTTPException(status_code=500, detail="FRONTEND_BASE_URL is not set")

        try:
            redirect_uri = f"{FRONTEND_BASE_URL.rstrip('/')}/auth/{provider}/callback/"

            if follow_redirect:
                return await client.authorize_redirect(request, redirect_uri)

            authorization_url = await client.create_authorization_url(redirect_uri)
            await client.save_authorize_data(
                request, redirect_uri=redirect_uri, **authorization_url
            )

            return authorization_url.get("url", None)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to initiate OAuth")

    @staticmethod
    async def handle_verified(
        provider: str, request: Request, db: Session
    ) -> HandleOauthResponse:
        client = oauth_config.get_client(provider)
        if not client:
            raise HTTPException(
                status_code=400, detail=f"Provider {provider} not supported"
            )

        try:
            token = await client.authorize_access_token(request)

            user_info = await OAuthService._get_user_info(client, token, provider)

            user, account, is_new_user = await OAuthService._find_or_create_user(
                db, provider, user_info, token
            )

            return {
                "user": user,
                "account": account,
                "is_new_user": is_new_user,
                "provider_user_info": user_info,
            }

        except Exception as e:
            traceback.print_exc()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=400,
                detail=f"OAuth verification for {provider} failed: {str(e)}",
            )

    @staticmethod
    async def _get_user_info(
        client, token: OAuthTokenResponse, provider: str
    ) -> UserInfoResponse:
        if provider == "github":
            return await OAuthService._get_github_user_info(client, token)
        else:
            raise HTTPException(
                status_code=400, detail=f"Provider {provider} not implemented"
            )

    @staticmethod
    async def _get_github_user_info(
        client, token: OAuthTokenResponse
    ) -> UserInfoResponse:
        user_response = await client.get("https://api.github.com/user", token=token)
        user_data = user_response.json()

        # Get user emails
        emails_response = await client.get(
            "https://api.github.com/user/emails", token=token
        )
        emails_data = (
            emails_response.json() if emails_response.status_code == 200 else []
        )

        primary_email: Optional[str] = None
        verified_email: Optional[str] = None

        for email in emails_data:
            if email.get("primary") and email.get("verified"):
                primary_email = email.get("email")
                break
            elif email.get("verified") and not verified_email:
                verified_email = email.get("email")

        final_email = primary_email or verified_email or user_data.get("email")

        return {
            "id": str(user_data["id"]),
            "username": user_data["login"],
            "email": final_email,
            "name": user_data.get("name"),
            "provider": "github",
        }

    @staticmethod
    async def _find_or_create_user(
        db: Session,
        provider: str,
        user_info: UserInfoResponse,
        token: OAuthTokenResponse,
    ) -> Tuple[User, Account, bool]:
        provider_id = user_info["id"]
        provider_email = user_info["email"]

        stmt = select(Account).where(
            Account.provider == provider, Account.provider_id == provider_id
        )
        existing_account = db.execute(stmt).scalar()

        if existing_account:
            OAuthService._update_account(existing_account, user_info, token)
            db.commit()
            return existing_account.user, existing_account, False

        user: Optional[User] = None
        if provider_email:
            stmt = select(User).where(User.username == provider_email)
            user = db.execute(stmt).scalar()

        is_new_user = False
        if not user:
            user = User(
                username=provider_email,
                password=generate_hash_password(""),
                is_active=True,
            )
            db.add(user)
            db.flush()
            is_new_user = True

        account = Account(
            user_id=user.id,
            provider=provider,
            provider_id=provider_id,
            provider_email=provider_email,
            provider_username=user_info.get("username"),
            provider_name=user_info.get("name"),
        )

        OAuthService._update_account_tokens(account, token)
        db.add(account)
        db.commit()

        return user, account, is_new_user

    @staticmethod
    def _update_account(
        account: Account, user_info: UserInfoResponse, token: OAuthTokenResponse
    ):
        if user_info.get("email") is not None:
            account.provider_email = user_info.get("email")

        if user_info.get("username") is not None:
            account.provider_username = user_info.get("username")

        if user_info.get("name") is not None:
            account.provider_name = user_info.get("name")

        account.updated_at = datetime.now(pytz.timezone(TZ))

        OAuthService._update_account_tokens(account, token)

    @staticmethod
    def _update_account_tokens(account: Account, token: OAuthTokenResponse):
        account.access_token = token.get("access_token")
        account.refresh_token = token.get("refresh_token")

        if token.get("expires_in"):
            account.token_expires_at = datetime.now(pytz.timezone(TZ)) + timedelta(
                seconds=int(token["expires_in"])
            )

        if token.get("token_type"):
            account.token_type = token.get("token_type")

        if token.get("scope"):
            account.scope = token.get("scope")
