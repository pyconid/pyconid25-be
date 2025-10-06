from pydantic import BaseModel, ConfigDict


NoContentResponse = None


class UnauthorizedResponse(BaseModel):
    message: str = "Unauthorized"


class BadRequestResponse(BaseModel):
    message: str


class ValidationErrorResponseDetail(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "message": "Terjadi kesalahan validasi pada data form (Pydantic validation).",
                "errors": [
                    {
                        "field": "bio",
                        "message": "String should have at least 10 characters",
                    },
                    {
                        "field": "phone",
                        "message": "Value error, Phone number must be in international format, e.g., +6281234567890.",
                    },
                ],
            }
        },
    )

    message: str
    error: list[ValidationErrorResponseDetail]


class ForbiddenResponse(BaseModel):
    message: str = "You don't have permissions to perform this action"


class NotFoundResponse(BaseModel):
    detail: str = "Not found"


class InternalServerErrorResponse(BaseModel):
    detail: str
