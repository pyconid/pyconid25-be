from typing import Optional
from fastapi import HTTPException

from sqlalchemy import select
from core.oauth.base import BaseOAuthService, OAuthTokenResponse, UserInfoResponse
from models.User import User
from sqlalchemy.orm import Session

from settings import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET


class OAuthGithubService(BaseOAuthService):
    def _get_provider_name(self) -> str:
        return "github"

    def _register_provider(self):
        if not GITHUB_CLIENT_SECRET or not GITHUB_CLIENT_ID:
            print("Warning: GitHub OAuth not configured - missing credentials")
            return

        self.oauth.register(
            name="github",
            client_id=GITHUB_CLIENT_ID,
            client_secret=GITHUB_CLIENT_SECRET,
            client_kwargs={"scope": "user:email"},
            authorize_url="https://github.com/login/oauth/authorize",
            access_token_url="https://github.com/login/oauth/access_token",
            userinfo_endpoint="https://api.github.com/user",
            api_base_url="https://api.github.com",
        )

    async def _get_user_info(
        self, client, token: OAuthTokenResponse
    ) -> UserInfoResponse:
        user_response = await client.get("https://api.github.com/user", token=token)
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=400, detail="Failed to fetch GitHub user info"
            )

        user_data = user_response.json()

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

        return UserInfoResponse(
            id=str(user_data.get("id")),
            username=user_data.get("login"),
            email=final_email,
            name=user_data.get("name"),
        )

    def _get_user_by_provider_id(self, db: Session, provider_id: str) -> Optional[User]:
        stmt = select(User).where(User.github_id == provider_id)
        return db.execute(stmt).scalar()

    def _update_user_provider_info(
        self, user: User, user_info: UserInfoResponse
    ) -> User:
        user.github_username = user_info.get("username")
        return user

    def _set_user_provider_fields(
        self, user_data: dict, user_info: UserInfoResponse, provider_id: str
    ) -> dict:
        user_data.update(
            {"github_id": provider_id, "github_username": user_info.get("username")}
        )
        if user_info.get("email"):
            user_data["email"] = user_info.get("email")

        return user_data
