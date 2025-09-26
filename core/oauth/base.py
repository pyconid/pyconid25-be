from datetime import datetime
import traceback
from abc import ABC, abstractmethod
from typing import Optional, Tuple, TypedDict, Union
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
import pytz
from sqlalchemy import or_, select
from models.User import User
from settings import FRONTEND_BASE_URL, TZ
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session


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


class BaseOAuthService(ABC):
    """Base OAuth service that must be inherited by all OAuth providers."""

    def __init__(self):
        self.oauth = OAuth()
        self._register_provider()

    @abstractmethod
    def _register_provider(self):
        """Register OAuth providers using authlib."""
        pass

    @abstractmethod
    async def _get_user_info(
        self, client, token: OAuthTokenResponse
    ) -> UserInfoResponse:
        """Get user info from the API provider."""
        pass

    @abstractmethod
    def _get_provider_name(self) -> str:
        """Return provider name (github, google, discord, etc)"""
        pass

    @abstractmethod
    def _get_user_by_provider_id(self, db: Session, provider_id: str) -> Optional[User]:
        """Find user by provider-specific ID field"""
        pass

    @abstractmethod
    def _update_user_provider_info(
        self, user: User, user_info: UserInfoResponse
    ) -> User:
        """Update user dengan provider-specific fields"""
        pass

    @abstractmethod
    def _set_user_provider_fields(
        self, user_data: dict, user_info: UserInfoResponse, provider_id: str
    ) -> dict:
        """Set provider-specific fields untuk user baru"""
        pass

    async def initiate_oauth(
        self, request: Request, follow_redirect: Optional[bool] = False
    ) -> Union[RedirectResponse, str]:
        """
        Initiate OAuth flow.

        The same general logic for all providers.
        """
        provider_name = self._get_provider_name()

        if not hasattr(self.oauth, provider_name):
            raise HTTPException(
                status_code=500,
                detail=f"OAuth provider '{provider_name}' is not properly configured",
            )

        client = getattr(self.oauth, provider_name)

        if FRONTEND_BASE_URL is None:
            raise HTTPException(status_code=500, detail="FRONTEND_BASE_URL is not set")

        try:
            redirect_uri = (
                f"{FRONTEND_BASE_URL.rstrip('/')}/auth/{provider_name}/callback/"
            )

            if follow_redirect:
                return await client.authorize_redirect(request, redirect_uri)

            authorization_url = await client.create_authorization_url(redirect_uri)
            await client.save_authorize_data(
                request, redirect_uri=redirect_uri, **authorization_url
            )

            return authorization_url.get("url", None)

        except Exception as e:
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initiate {provider_name} OAuth: {str(e)}",
            )

    async def handle_verified(
        self, request: Request, db: Session
    ) -> HandleOauthResponse:
        """
        Handle OAuth callbacks and create/update users.

        The same general logic for all providers.
        Provider-specific logic is delegated to abstract methods.
        """
        provider_name = self._get_provider_name()

        if not hasattr(self.oauth, provider_name):
            raise HTTPException(
                status_code=500,
                detail=f"OAuth provider '{provider_name}' is not properly configured",
            )

        client = getattr(self.oauth, provider_name)

        try:
            # Get access token
            token = await client.authorize_access_token(request)

            # Get user info from provider
            user_info = await self._get_user_info(client, token)

            # Find or create user
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
                detail=f"OAuth verification for {provider_name} failed: {str(e)}",
            )

    async def _find_or_create_user(
        self, db: Session, user_info: UserInfoResponse
    ) -> Tuple[User, bool]:
        """
        Common user finding/creation logic.
        """
        provider_id = user_info.get("id")
        provider_username = user_info.get("username")
        provider_email = user_info.get("email")

        existing_user = self._get_user_by_provider_id(db, provider_id)

        if existing_user:
            # Update existing user info
            updated_user = self._update_user_provider_info(existing_user, user_info)
            updated_user.updated_at = datetime.now(pytz.timezone(TZ))
            db.commit()
            return updated_user, False

        user: Optional[User] = None
        if provider_email:
            stmt = select(User).where(
                or_(
                    User.username == provider_email, User.google_email == provider_email
                )
            )
            user = db.execute(stmt).scalar()

        is_new_user = False

        if not user:
            user_data = {
                "username": provider_email if provider_email else provider_username,
                "password": None,
                "is_active": True,
                "created_at": datetime.now(pytz.timezone(TZ)),
                "updated_at": datetime.now(pytz.timezone(TZ)),
            }

            # Set provider-specific fields
            user_data = self._set_user_provider_fields(
                user_data, user_info, provider_id
            )

            user = User(**user_data)
            db.add(user)
            db.flush()
            is_new_user = True

        else:
            user = self._update_user_provider_info(user, user_info)

            user.updated_at = datetime.now(pytz.timezone(TZ))
            db.add(user)

        db.commit()
        return user, is_new_user
