from fastapi import Depends, Form, UploadFile
from typing import Optional
from pydantic import EmailStr, HttpUrl
from core.security import get_current_user
from models.User import User
from schemas.user_profile import (
    Gender,
    IndustryCategory,
    JobCategory,
    TShirtSize,
    LookingForOption,
    UserProfileCreate,
)
from datetime import date


def save_file_and_get_url(url: Optional[UploadFile]) -> Optional[str]:
    if url:
        # Simulasi penyimpanan file dan mendapatkan URL
        return f"https://example.com/files/{url.filename}"
    return None


def get_user_form(
    # (1) Dependency autentikasi dijalankan PERTAMA
    user: User = Depends(get_current_user),
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
    country: str = Form(...),
    state: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
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
):
    if user is None:
        return None, None
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
        country=country,
        state=state,
        city=city,
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
    return user_profile_pydantic, user
