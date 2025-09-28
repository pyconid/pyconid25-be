from pydantic import BaseModel


NoContentResponse = None


class UnauthorizedResponse(BaseModel):
    message: str = "Unauthorized"


class BadRequestResponse(BaseModel):
    message: str


class ValidationErrorResponseDetail(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    message: str
    error: list[ValidationErrorResponseDetail]

    class Config:
        # Konfigurasi agar model dapat digunakan dengan ORM
        from_attributes = True
        # Membuat contoh data untuk dokumentasi API
        json_schema_extra = {
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
        }


class ForbiddenResponse(BaseModel):
    message: str = "You don't have permissions to perform this action"


class NotFoundResponse(BaseModel):
    detail: str = "Not found"


class InternalServerErrorResponse(BaseModel):
    detail: str
