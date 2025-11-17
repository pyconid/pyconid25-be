from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from models.Speaker import Speaker
from models.SpeakerType import SpeakerType
from schemas.speaker import SpeakerResponseItem


def get_all_speakers(db: Session):
    # Query dasar
    stmt = select(Speaker)

    # Tambahkan pagination (offset + limit)
    # Hitung total data sebelum pagination
    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))
    # Eksekusi query dan ambil hasilnya
    results = db.scalars(stmt).all()
    # 🔥 ubah ORM objects ke Pydantic models
    results_schema = [SpeakerResponseItem.model_validate(r) for r in results]
    # Hitung total halaman

    # Return hasil dalam bentuk dict (siap untuk API response)
    return {
        "page": 1,
        "page_size": 1,
        "count": total_count,  # total_count,
        "page_count": 1,  # page_count,
        "results": results_schema,
    }


def get_speaker_per_page_by_search(
    db: Session,
    page: int,
    page_size: int,
    search: Optional[str] = None,
):
    # Hitung offset (data mulai dari baris ke-berapa)
    offset = (page - 1) * page_size

    # Query dasar
    stmt = select(Speaker)

    # Jika ada keyword pencarian
    if search:
        stmt = stmt.where(
            Speaker.name.ilike(f"%{search}%"),
        )

    # Hitung total data sebelum pagination
    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))

    # Tambahkan pagination (offset + limit)
    stmt = stmt.offset(offset).limit(page_size)

    # Eksekusi query dan ambil hasilnya
    results = db.scalars(stmt).all()
    # 🔥 ubah ORM objects ke Pydantic models
    results_schema = [SpeakerResponseItem.model_validate(r) for r in results]
    # Hitung total halaman
    page_count = (total_count + page_size - 1) // page_size if total_count else 0

    # Return hasil dalam bentuk dict (siap untuk API response)
    return {
        "page": page,
        "page_size": page_size,
        "count": total_count,  # total_count,
        "page_count": page_count,  # page_count,
        "results": results_schema,
    }


def get_speaker_by_id(db: Session, id: str) -> Optional[Speaker]:
    stmt = select(Speaker).where(Speaker.id == id)
    return db.execute(stmt).scalar()


def create_speaker(
    db: Session,
    name: str,
    bio: Optional[str] = None,
    photo_url: Optional[str] = None,
    email: Optional[str] = None,
    instagram_link: Optional[str] = None,
    x_link: Optional[str] = None,
    speaker_type: Optional[SpeakerType] = None,
    is_commit: bool = True,
) -> Speaker:
    new_speaker = Speaker(
        name=name,
        bio=bio,
        email=email,
        instagram_link=instagram_link,
        x_link=x_link,
        speaker_type=speaker_type,
        photo_url=photo_url,
    )
    db.add(new_speaker)
    if is_commit:
        db.commit()
    return new_speaker


def update_speaker(
    db: Session,
    speaker: Speaker,
    name: str,
    bio: Optional[str] = None,
    photo_url: Optional[str] = None,
    email: Optional[str] = None,
    instagram_link: Optional[str] = None,
    x_link: Optional[str] = None,
    speaker_type: Optional[SpeakerType] = None,
    is_commit: bool = True,
) -> Speaker:
    speaker.name = name
    speaker.bio = bio
    if photo_url is not None:
        speaker.photo_url = photo_url
    speaker.email = email
    speaker.instagram_link = instagram_link
    speaker.x_link = x_link
    speaker.speaker_type = speaker_type
    if is_commit:
        db.commit()
    return speaker


def delete_speaker(
    db: Session,
    speaker: Speaker,
    is_commit: bool = True,
) -> None:
    db.delete(speaker)
    if is_commit:
        db.commit()
