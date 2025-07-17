from datetime import datetime
import traceback
from typing import Optional, Tuple, TypedDict, Union
from fastapi import HTTPException, Request

from fastapi.responses import RedirectResponse
import pytz
from sqlalchemy import select
from models.User import User
from settings import FRONTEND_BASE_URL, TZ
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session

from settings import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET


class UserInfoResponse(TypedDict):
    id: str
    username: str
    email: Optional[str]
    name: Optional[str]


class HandleOauthResponse(TypedDict):
    user: User
    is_new_user: bool
    provider_user_info: UserInfoResponse


class OAuthTokenResponse(TypedDict, total=False):
    access_token: str
    refresh_token: Optional[str]
    expires_in: Optional[int]
    token_type: Optional[str]
    scope: Optional[str]


class OAuthGithubService:
    def __init__(self):
        self.oauth = OAuth()
        self.base_url_github = "https://github.com"
        self.api_base_url_github = "https://api.github.com"

        self._register_providers()

    def _register_providers(self):
        if GITHUB_CLIENT_SECRET and GITHUB_CLIENT_ID:
            self.oauth.register(
                name="github",
                client_id=GITHUB_CLIENT_ID,
                client_secret=GITHUB_CLIENT_SECRET,
                client_kwargs={"scope": "user:email"},
                authorize_url=f"{self.base_url_github}/login/oauth/authorize",
                access_token_url=f"{self.base_url_github}/login/oauth/access_token",
                userinfo_endpoint=f"{self.api_base_url_github}/user",
                emails_endpoint=f"{self.api_base_url_github}/user/emails",
                api_base_url=self.api_base_url_github,
            )

    async def initiate_oauth(
        self, request: Request, follow_redirect: Optional[bool] = False
    ) -> Union[RedirectResponse, str]:
        client = self.oauth.github

        if FRONTEND_BASE_URL is None:
            raise HTTPException(status_code=500, detail="FRONTEND_BASE_URL is not set")

        try:
            redirect_uri = f"{FRONTEND_BASE_URL.rstrip('/')}/auth/github/callback/"

            if follow_redirect:
                return await client.authorize_redirect(request, redirect_uri)

            authorization_url = await client.create_authorization_url(redirect_uri)
            await client.save_authorize_data(
                request, redirect_uri=redirect_uri, **authorization_url
            )

            return authorization_url.get("url", None)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to initiate OAuth")

    async def handle_verified(
        self, request: Request, db: Session
    ) -> HandleOauthResponse:
        client = self.oauth.github

        try:
            token = await client.authorize_access_token(request)

            user_info = await self._get_github_user_info(client, token)

            user, is_new_user = await self._find_or_create_user(db, user_info)

            return {
                "user": user,
                "is_new_user": is_new_user,
                "provider_user_info": user_info,
            }

        except Exception as e:
            traceback.print_exc()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=400,
                detail=f"OAuth verification for github failed: {str(e)}",
            )

    async def _get_github_user_info(
        self, client, token: OAuthTokenResponse
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
            "id": str(user_data.get("id")),
            "username": user_data.get("login"),
            "email": final_email,
            "name": user_data.get("name"),
        }

    async def _find_or_create_user(
        self,
        db: Session,
        user_info: UserInfoResponse,
    ) -> Tuple[User, bool]:
        provider_id = user_info.get("id")
        provider_email = user_info.get("email")

        stmt = select(User).where(User.github_id == provider_id)
        existing_user = db.execute(stmt).scalar()
        if existing_user:
            existing_user.github_username = user_info.get("username")
            existing_user.updated_at = datetime.now(pytz.timezone(TZ))

            return existing_user, False

        user: Optional[User] = None
        if provider_email:
            stmt = select(User).where(User.username == provider_email)
            user = db.execute(stmt).scalar()

        is_new_user = False
        if not user:
            user = User(
                username=user_info.get("username"),
                password=None,
                github_id=provider_id,
                github_username=user_info.get("username"),
                is_active=True,
                created_at=datetime.now(pytz.timezone(TZ)),
                updated_at=datetime.now(pytz.timezone(TZ)),
            )
            db.add(user)
            db.flush()
            is_new_user = True

        if not is_new_user:
            if user_info.get("username") is not None:
                user.github_username = user_info.get("username")

            user.github_id = provider_id
            user.updated_at = datetime.now(pytz.timezone(TZ))
            db.add(user)

        db.commit()

        return user, is_new_user


oauth_github_service = OAuthGithubService()
