from typing import Optional
from fastapi import HTTPException

from sqlalchemy import select
from core.oauth.base import BaseOAuthService, OAuthTokenResponse, UserInfoResponse
from models.User import User
from sqlalchemy.orm import Session

from settings import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET


class OAuthGoogleService(BaseOAuthService):
    def _get_provider_name(self) -> str:
        return "google"

    def _register_provider(self):
        if not GOOGLE_CLIENT_SECRET or not GOOGLE_CLIENT_ID:
            print("Warning: Google OAuth not configured - missing credentials")
            return

        self.oauth.register(
            name="google",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            client_kwargs={"scope": "openid email profile", "prompt": "select_account"},
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        )

    async def _get_user_info(
        self, client, token: OAuthTokenResponse
    ) -> UserInfoResponse:
        try:
            user_response = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo", token=token
            )

            if user_response.status_code != 200:
                user_response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo", token=token
                )

            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=400, detail="Failed to fetch Google user info"
                )
        except HTTPException as http_exception:
            raise http_exception
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to fetch Google user info: {str(e)}"
            )

        user_data = user_response.json()

        return UserInfoResponse(
            id=str(user_data.get("sub") or user_data.get("id")),
            username=user_data.get("email"),
            email=user_data.get("email"),
            name=user_data.get("name"),
        )

    def _get_user_by_provider_id(self, db: Session, provider_id: str) -> Optional[User]:
        stmt = select(User).where(User.google_id == provider_id)
        return db.execute(stmt).scalar()

    def _update_user_provider_info(
        self, user: User, user_info: UserInfoResponse
    ) -> User:
        user.google_email = user_info.get("email")
        return user

    def _set_user_provider_fields(
        self, user_data: dict, user_info: UserInfoResponse, provider_id: str
    ) -> dict:
        user_data.update(
            {"google_id": provider_id, "google_email": user_info.get("email")}
        )
        return user_data
