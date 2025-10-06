from datetime import date
from typing import Optional
from fastapi import Form, UploadFile, File
from fastapi import APIRouter, Depends
from pydantic import EmailStr, HttpUrl
from core.helper import save_file_and_get_url
from models.User import User
from schemas.user_profile import (
    Gender,
    IndustryCategory,
    JobCategory,
    LookingForOption,
    TShirtSize,
    UserProfileCreate,
    UserProfileDB,
    UserProfileEditSuccessResponse,
    UserProfilePrivate,
)
from sqlalchemy.orm import Session
from core.responses import (
    BadRequest,
    InternalServerError,
    common_response,
    Unauthorized,
)
from core.security import (
    get_current_user,
)
from models import get_db_sync
from schemas.common import (
    BadRequestResponse,
    InternalServerErrorResponse,
    UnauthorizedResponse,
    ValidationErrorResponse,
)
from repository import user as userRepo
from validators.location import LocationValidationError, validate_location_hierarchy

router = APIRouter(prefix="/user-profile", tags=["UserProfile"])

# === PUT endpoint ===


@router.put(
    "/",
    responses={
        "200": {"model": UserProfileEditSuccessResponse},
        "400": {"model": BadRequestResponse},
        "422": {"model": ValidationErrorResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def update_user_profile(
    profile_picture: UploadFile = File(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: Optional[EmailStr] = Form(None),
    industry_categories: Optional[IndustryCategory] = Form(None),
    company: Optional[str] = Form(None),
    job_category: JobCategory = Form(...),
    job_title: str = Form(...),
    experience: Optional[int] = Form(None),
    t_shirt_size: Optional[TShirtSize] = Form(None),
    gender: Optional[Gender] = Form(None),
    date_of_birth: Optional[date] = Form(None),
    phone: Optional[str] = Form(None),
    country_id: int = Form(...),
    state_id: Optional[int] = Form(None),
    city_id: Optional[int] = Form(None),
    zip_code: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    bio: str = Form(...),
    interest: Optional[str] = Form(None),  # comma separated
    looking_for: Optional[LookingForOption] = Form(None),
    expertise: Optional[str] = Form(None),  # comma separated
    website: Optional[HttpUrl] = Form(None),
    github_username: Optional[str] = Form(None),
    facebook_username: Optional[str] = Form(None),
    linkedin_username: Optional[str] = Form(None),
    twitter_username: Optional[str] = Form(None),
    instagram_username: Optional[str] = Form(None),
    coc_acknowledged: bool = Form(...),
    terms_agreed: bool = Form(...),
    privacy_agreed: bool = Form(...),
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    if user is None:
        return common_response(Unauthorized(message="Unauthorized"))

    if country_id:
        try:
            validate_location_hierarchy(
                db=db,
                country_id=country_id,
                state_id=state_id,
                city_id=city_id,
                zip_code=zip_code,
            )
        except LocationValidationError as e:
            return common_response(BadRequest(message=str(e)))

    # semua field dari UserProfileCreate.
    user_profile_pydantic = UserProfileCreate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        industry_categories=industry_categories,
        company=company,
        job_category=job_category,
        job_title=job_title,
        experience=experience,
        t_shirt_size=t_shirt_size,
        gender=gender,
        date_of_birth=date_of_birth,
        phone=phone,
        country_id=country_id,
        state_id=state_id,
        city_id=city_id,
        zip_code=zip_code,
        address=address,
        bio=bio,
        interest=interest,
        looking_for=looking_for,
        expertise=expertise,
        website=website,
        github_username=github_username,
        facebook_username=facebook_username,
        linkedin_username=linkedin_username,
        twitter_username=twitter_username,
        instagram_username=instagram_username,
        coc_acknowledged=coc_acknowledged,
        terms_agreed=terms_agreed,
        privacy_agreed=privacy_agreed,
    )
    # 1. Simpan file dan dapatkan URL
    profile_picture_url = save_file_and_get_url(profile_picture)

    # 2. Gabungkan data. user_form.model_dump() akan berisi
    user_profile_dict = user_profile_pydantic.model_dump()
    user_profile_dict["profile_picture"] = profile_picture_url

    # 3. Validasi dengan model DB
    # UserProfileDB akan mengharapkan semua field dari Create + profile_picture
    validated_profile = UserProfileDB(**user_profile_dict)

    # ... simpan ke database ...
    # Simpan ke posgres
    try:
        userRepo.update_user_profile(
            db=db, user_id=user.id, profile_data=validated_profile
        )
    except Exception as e:
        return common_response(
            InternalServerError(error=f"Failed to update profile {str(e)}")
        )

    return validated_profile


# === GET endpoint ===


@router.get(
    "/",
    responses={
        "200": {"model": UserProfilePrivate},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_user_profile(user: User = Depends(get_current_user)):
    if user is None:
        return common_response(Unauthorized(message="Unauthorized"))
    user_schema = UserProfilePrivate.model_validate(user)
    return user_schema
