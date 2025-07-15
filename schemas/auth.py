from typing import Optional
from fastapi import Query
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginSuccessResponse(BaseModel):
    id: str
    username: str
    is_active: bool
    token: str
    refresh_token: str


class MeResponse(BaseModel):
    id: str
    username: str


class LogoutSuccessResponse(BaseModel):
    message: str


class OauthSignInRequest(BaseModel):
    follow_redirect: Optional[bool] = Field(Query(False, description="Follow redirect"))


class OAuthSignInResponse(BaseModel):
    redirect_url: str


class OAuthCallbackResponse(BaseModel):
    id: str
    username: str
    is_active: bool
    token: str
    refresh_token: str
    is_new_user: bool
    provider: str
    provider_username: Optional[str]
    provider_email: Optional[str]
    provider_name: Optional[str]


class GitHubVerifiedRequest(BaseModel):
    github_cookie: str


class GitHubVerifiedResponse(BaseModel):
    id: str
    github_username: str
    token: str
    refresh_token: str
    username: str
    is_active: bool
