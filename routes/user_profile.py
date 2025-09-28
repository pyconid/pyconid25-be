from fastapi import UploadFile, File
from fastapi import APIRouter, Depends
from core.helper import get_user_form, save_file_and_get_url
from models.User import User
from schemas.user_profile import (
    UserProfileDB,
    UserProfileEditSuccessResponse,
    UserProfilePublic,
    UserProfilePrivate,
)
from sqlalchemy.orm import Session
from core.responses import (
    InternalServerError,
    common_response,
    Ok,
    Unauthorized,
)
from core.security import (
    get_current_user,
)
from models import get_db_sync
from schemas.common import (
    InternalServerErrorResponse,
    ValidationErrorResponse,
)
from repository import user as userRepo

router = APIRouter(prefix="/user-profile", tags=["UserProfile"])

# === PUT endpoint ===


@router.put(
    "/",
    responses={
        "200": {"model": UserProfileEditSuccessResponse},
        "422": {"model": ValidationErrorResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def update_user_profile(
    profile_picture: UploadFile = File(...),
    form_and_user: tuple = Depends(get_user_form),
    db: Session = Depends(get_db_sync),
):
    user_form, user = form_and_user
    if user_form is None:
        return common_response(Unauthorized(message="Unauthorized"))
    # 1. Simpan file dan dapatkan URL
    profile_picture_url = save_file_and_get_url(profile_picture)

    # 2. Gabungkan data. user_form.model_dump() akan berisi
    #    semua field dari UserProfileBase.
    user_data_complete = user_form.model_dump()
    user_data_complete["profile_picture"] = profile_picture_url

    # 3. Validasi dengan model DB
    # UserProfileDB akan mengharapkan semua field dari Base + profile_picture
    validated_profile = UserProfileDB(**user_data_complete)

    # ... simpan ke database ...
    # Simpan ke posgres
    try:
        userRepo.update_user_profile(
            db=db, user_id=user.id, profile_data=validated_profile.model_dump()
        )
    except Exception as e:
        return common_response(
            InternalServerError(error=f"Failed to update profile {str(e)}")
        )

    return common_response(Ok(data="Profile updated successfully"))


# === GET endpoint ===


@router.get("/{username}")
async def get_user_profile(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_sync),
):
    if user is None or user.username != username:
        user = userRepo.get_user_by_username(db=db, username=username)
        user_schema = UserProfilePublic.model_validate(user)
        return user_schema
    user_schema = UserProfilePrivate.model_validate(user)
    return user_schema
