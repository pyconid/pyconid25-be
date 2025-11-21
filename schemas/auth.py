from typing import Optional
from fastapi import Query
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginEmailRequest(BaseModel):
    email: str
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
    participant_type: Optional[str] = None


class LogoutSuccessResponse(BaseModel):
    message: str


class SignUpRequest(BaseModel):
    email: str
    username: str
    password: str


class EmailVerifiedSuccessResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ForgotPasswordSuccessResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ResetPasswordSuccessResponse(BaseModel):
    message: str


class OauthSignInRequest(BaseModel):
    follow_redirect: Optional[bool] = Field(Query(False, description="Follow redirect"))


class GithubSignInResponse(BaseModel):
    redirect: str


class GithubVerifiedResponse(BaseModel):
    id: str
    username: str
    is_active: bool
    token: str
    refresh_token: str
    is_new_user: bool
    github_username: str


class GoogleSignInResponse(BaseModel):
    redirect: str


class GoogleVerifiedResponse(BaseModel):
    id: str
    username: str
    is_active: bool
    token: str
    refresh_token: str
    is_new_user: bool
    google_email: str
