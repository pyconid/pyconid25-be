import uuid
from models import Base
from sqlalchemy import UUID, DateTime, String, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column("username", String, nullable=True)
    password: Mapped[str] = mapped_column("password", String, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        "is_active", Boolean, nullable=True, default=False
    )
    github_id: Mapped[str] = mapped_column(
        "github_id", String(255), nullable=True, index=True
    )
    github_username: Mapped[str] = mapped_column(
        "github_username", String(255), nullable=True
    )
    google_id: Mapped[str] = mapped_column(
        "google_id", String(255), nullable=True, index=True
    )
    google_email: Mapped[str] = mapped_column(
        "google_email", String(255), nullable=True
    )
    profile_picture: Mapped[str] = mapped_column(
        "profile_picture", String, nullable=True
    )
    first_name: Mapped[str] = mapped_column("first_name", String, nullable=True)
    last_name: Mapped[str] = mapped_column("last_name", String, nullable=True)
    email: Mapped[str] = mapped_column("email", String, nullable=True)
    industry_categories: Mapped[str] = mapped_column(
        "industry_categories", String, nullable=True
    )
    company: Mapped[str] = mapped_column("company", String, nullable=True)
    job_category: Mapped[str] = mapped_column("job_category", String, nullable=True)
    job_title: Mapped[str] = mapped_column("job_title", String, nullable=True)
    experience: Mapped[int] = mapped_column("experience", String, nullable=True)
    t_shirt_size: Mapped[str] = mapped_column("t_shirt_size", String, nullable=True)
    gender: Mapped[str] = mapped_column("gender", String, nullable=True)
    date_of_birth: Mapped[str] = mapped_column("date_of_birth", String, nullable=True)
    phone: Mapped[str] = mapped_column("phone", String, nullable=True)
    country: Mapped[str] = mapped_column("country", String, nullable=True)
    state: Mapped[str] = mapped_column("state", String, nullable=True)
    city: Mapped[str] = mapped_column("city", String, nullable=True)
    zip_code: Mapped[int] = mapped_column("zip_code", String, nullable=True)
    address: Mapped[str] = mapped_column("address", String, nullable=True)
    bio: Mapped[str] = mapped_column("bio", String, nullable=True)
    interest: Mapped[str] = mapped_column("interest", String, nullable=True)
    looking_for: Mapped[str] = mapped_column("looking_for", String, nullable=True)
    expertise: Mapped[str] = mapped_column("expertise", String, nullable=True)
    website: Mapped[str] = mapped_column("website", String, nullable=True)
    facebook_username: Mapped[str] = mapped_column(
        "facebook_username", String, nullable=True
    )
    linkedin_username: Mapped[str] = mapped_column(
        "linkedin_username", String, nullable=True
    )
    twitter_username: Mapped[str] = mapped_column(
        "twitter_username", String, nullable=True
    )
    instagram_username: Mapped[str] = mapped_column(
        "instagram_username", String, nullable=True
    )
    terms_agreed: Mapped[bool] = mapped_column(
        "terms_agreed", Boolean, nullable=True, default=False
    )
    privacy_agreed: Mapped[bool] = mapped_column(
        "privacy_agreed", Boolean, nullable=True, default=False
    )
    coc_acknowledged: Mapped[bool] = mapped_column(
        "coc_acknowledged", Boolean, nullable=True, default=False
    )
    participant_type: Mapped[str] = mapped_column(
        "participant_type", String, nullable=True, default="Non Participant"
    )

    created_at = mapped_column("created_at", DateTime(timezone=True))
    updated_at = mapped_column("updated_at", DateTime(timezone=True))
    deleted_at = mapped_column("deleted_at", DateTime(timezone=True))

    # One to Many
    tokens = relationship("Token", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
