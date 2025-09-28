import re
from datetime import date
from enum import Enum
from typing import Optional, List, Any

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator

# --- Enums for Dropdown Fields ---
# Menggunakan Enum memastikan data yang masuk adalah salah satu dari opsi yang valid.


class IndustryCategory(str, Enum):
    TECHNOLOGY = "Technology"
    FINANCE = "Finance"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"


class JobCategory(str, Enum):
    TECH_SPECIALIST = "Tech - Specialist"
    MANAGEMENT = "Management"
    DESIGN = "Design"
    MARKETING = "Marketing"


class TShirtSize(str, Enum):
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"


class LookingForOption(str, Enum):
    OPEN_OPPORTUNITIES = "Open Opportunities"
    NETWORKING = "Networking"
    HIRING = "Hiring"
    MENTORSHIP = "Mentorship"


# --- Main Pydantic Model For DB---


class UserProfilePublic(BaseModel):
    """Model untuk data publik yang bisa dilihat semua orang."""

    profile_picture: Optional[HttpUrl] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_category: Optional[JobCategory] = None
    job_title: Optional[str] = None
    country: Optional[str] = None
    bio: Optional[str] = None
    # Default True, karena semua user adalah peserta
    participant_type: Optional[str] = "Non Participant"
    # Default True, karena semua user setuju CoC
    coc_acknowledged: Optional[bool] = False
    # Default True, karena semua user setuju Terms
    terms_agreed: Optional[bool] = False
    # Default True, karena semua user setuju Privacy
    privacy_agreed: Optional[bool] = False
    # 1. Buat Model BASE dengan semua field yang sama

    class Config:
        # Konfigurasi agar model dapat digunakan dengan ORM
        from_attributes = True


class UserProfilePrivate(UserProfilePublic):
    """Model untuk data privat yang hanya bisa dilihat oleh user itu sendiri."""

    """Berisi semua field umum yang diisi oleh user dari form."""

    email: Optional[EmailStr]

    # Professional Info
    industry_categories: Optional[IndustryCategory]
    company: Optional[str]
    experience: Optional[int]

    # Personal Details
    t_shirt_size: Optional[TShirtSize]
    gender: Optional[Gender]
    date_of_birth: Optional[date]
    phone: Optional[str]
    # Location
    # Di-handle dengan API, tapi tetap string
    state: Optional[str]
    city: Optional[str]
    zip_code: Optional[str]
    address: Optional[str]

    # Interests and Expertise
    interest: Optional[List[str]]
    looking_for: Optional[LookingForOption]
    expertise: Optional[List[str]]

    # Social & Portfolio
    website: Optional[HttpUrl]
    github_username: Optional[str]
    facebook_username: Optional[str]
    linkedin_username: Optional[str]
    twitter_username: Optional[str]
    instagram_username: Optional[str]

    class Config:
        # Konfigurasi agar model dapat digunakan dengan ORM
        from_attributes = True


class UserProfileBase(BaseModel):
    """Berisi semua field umum yang diisi oleh user dari form."""

    first_name: str = Field(
        ..., min_length=1, max_length=50, description="User's first name."
    )
    last_name: str = Field(
        ..., min_length=1, max_length=50, description="User's last name."
    )
    email: Optional[EmailStr] = Field(None, description="User's email address.")
    bio: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Short biography about the user.",
    )

    # Professional Info
    industry_categories: Optional[IndustryCategory] = None
    company: Optional[str] = Field(
        None, max_length=100, description="Company or organization name."
    )
    job_category: JobCategory = Field(..., description="Category of the user's job.")
    job_title: str = Field(..., max_length=100, description="User's job title.")
    experience: Optional[int] = Field(
        None, ge=0, description="Years of professional experience."
    )

    # Personal Details
    t_shirt_size: Optional[TShirtSize] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    phone: Optional[str] = Field(
        None, description="Phone number including country code (e.g., +6281234567890)."
    )
    participant_type: Optional[str] = Field(
        "Non Participant", description="Type of participant."
    )
    # Location
    # Di-handle dengan API, tapi tetap string
    country: str = Field(..., description="User's country.")
    state: Optional[str] = Field(None, description="User's state/province.")
    city: Optional[str] = Field(None, description="User's city.")
    zip_code: Optional[str] = Field(
        None, max_length=10, description="Postal or zip code."
    )
    address: Optional[str] = Field(None, max_length=255, description="Full address.")

    # Interests and Expertise
    interest: Optional[List[str]] = Field(None, description="List of user's interests.")
    looking_for: Optional[LookingForOption] = None
    expertise: Optional[List[str]] = Field(
        None, description="List of skills user is offering or searching for."
    )

    # Social & Portfolio
    website: Optional[HttpUrl] = None
    github_username: Optional[str] = None
    facebook_username: Optional[str] = None
    linkedin_username: Optional[str] = None
    twitter_username: Optional[str] = None
    instagram_username: Optional[str] = None

    # Agreements
    coc_acknowledged: bool = Field(..., description="Code of Conduct acknowledgement.")
    terms_agreed: bool = Field(..., description="Terms and Conditions agreement.")
    privacy_agreed: bool = Field(..., description="Privacy Policy agreement.")
    # --- Custom Validators (V2 Syntax) ---

    @field_validator("phone", mode="before")
    def validate_phone_number(cls, v: Any) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^\+[1-9]\d{1,14}$", str(v)):
            raise ValueError(
                "Phone number must be in international format, e.g., +6281234567890."
            )
        return str(v)

    # Satu validator untuk semua field tags
    @field_validator("interest", "expertise", mode="before")
    def split_tags(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(",") if tag.strip()]
        if isinstance(v, list):
            return v
        raise ValueError("Tags must be a comma-separated string or a list of strings.")

    # Satu validator untuk semua username
    @field_validator(
        "github_username",
        "facebook_username",
        "linkedin_username",
        "twitter_username",
        "instagram_username",
        mode="before",
    )
    def validate_username(cls, v: Any) -> Optional[str]:
        if v is None:
            return v
        if "://" in str(v) or "/" in str(v):
            raise ValueError("Please provide only the username, not the full URL.")
        return str(v)

    # Satu validator untuk semua checkbox agreement
    @field_validator("coc_acknowledged", "terms_agreed", "privacy_agreed")
    def must_be_true(cls, v: Any) -> bool:
        if v is not True:
            raise ValueError("This field must be checked to proceed.")
        return v


# 2. Model CREATE mewarisi dari BASE


class UserProfileCreate(UserProfileBase):
    """Model untuk validasi data mentah dari form. Tidak ada field tambahan."""

    pass


# 3. Model DB juga mewarisi dari BASE dan menambahkan field baru


class UserProfileDB(UserProfileBase):
    """
    Model yang merepresentasikan data lengkap di database.
    Mewarisi semua dari Base dan menambahkan field 'profile_picture'.
    """

    # Profile Info
    profile_picture: HttpUrl = Field(..., description="URL to the profile picture.")


class UserProfileEditSuccessResponse(UserProfileDB):
    class Config:
        # Konfigurasi agar model dapat digunakan dengan ORM
        from_attributes = True
        # Membuat contoh data untuk dokumentasi API
        json_schema_extra = {
            "example": {
                "profile_picture": "https://example.com/image.png",
                "first_name": "Budi",
                "last_name": "Santoso",
                "email": "budi.santoso@example.com",
                "bio": "Passionate software engineer with 5 years of experience in backend development.",
                "industry_categories": "Technology",
                "company": "Tech Corp",
                "job_category": "Tech - Specialist",
                "job_title": "Senior Software Engineer",
                "experience": 5,
                "t_shirt_size": "L",
                "gender": "Male",
                "date_of_birth": "1995-08-17",
                "phone": "+6281234567890",
                "country": "Indonesia",
                "state": "West Java",
                "city": "Bandung",
                "zip_code": "40111",
                "address": "Jl. Asia Afrika No. 1",
                "interest": "python, fastapi, docker",
                "looking_for": "Open Opportunities",
                "expertise": "backend, devops",
                "website": "https://budisantoso.dev",
                "github_username": "budisdev",
                "linkedin_username": "budisantoso",
                "coc_acknowledged": True,
                "terms_agreed": True,
                "privacy_agreed": True,
            }
        }


# --- Contoh Penggunaan ---
if __name__ == "__main__":
    # 1. Contoh data valid
    valid_data = {
        "profile_picture": "https://example.com/profile.jpg",
        "first_name": "Citra",
        "last_name": "Wijaya",
        "email": "citra.w@email.com",
        "bio": "A creative designer focused on user experience and interface design.",
        "job_category": "Design",
        "job_title": "UI/UX Designer",
        "country": "Indonesia",
        "interest": "figma, design thinking, user research",  # Akan diubah jadi list
        "coc_acknowledged": True,
        "terms_agreed": True,
        "privacy_agreed": True,
    }

    try:
        profile = UserProfileDB(**valid_data)
        print("✅ Data valid!")
        print(profile.model_dump_json(indent=2))
        # Cek hasil konversi tags
        print(f"\nInterests as list: {profile.interest}")
    except Exception as e:
        print("❌ Gagal validasi data valid:")
        print(e)

    print("\n" + "-" * 50 + "\n")

    # 2. Contoh data tidak valid
    invalid_data = {
        "profile_picture": "not-a-url",  # URL tidak valid
        "first_name": "Andi",
        "last_name": "Pratama",
        "email": "andi@.com",  # Email tidak valid
        "bio": "Too short",  # Bio terlalu pendek (min_length=10)
        "job_category": "Tech - Specialist",
        "job_title": "Developer",
        "country": "Indonesia",
        "phone": "081234567890",  # Format telepon salah
        "github_username": "https://github.com/andipratama",  # Seharusnya username saja
        "coc_acknowledged": False,  # Harus True
        "terms_agreed": True,
        "privacy_agreed": True,
    }

    try:
        profile = UserProfileDB(**invalid_data)
    except Exception as e:
        print("❌ Gagal validasi data tidak valid (sesuai harapan):")
        print(e)
