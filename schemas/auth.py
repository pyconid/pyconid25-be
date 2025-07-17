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


class GithubSignInResponse(BaseModel):
    redirect_url: str


class GithubVerifiedResponse(BaseModel):
    id: str
    username: str
    is_active: bool
    token: str
    refresh_token: str
    is_new_user: bool
    github_username: str
