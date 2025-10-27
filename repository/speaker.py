from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from models.Speaker import Speaker
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
