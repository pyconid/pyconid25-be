from pydantic import BaseModel


NoContentResponse = None


class UnauthorizedResponse(BaseModel):
    message: str = "Unauthorized"


class BadRequestResponse(BaseModel):
    message: str


class ForbiddenResponse(BaseModel):
    message: str = "You don't have permissions to perform this action"


class NotFoundResponse(BaseModel):
    detail: str = "Not found"


class InternalServerErrorResponse(BaseModel):
    detail: str
