from pydantic import BaseModel


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
