from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload
from models.Schedule import Schedule
from schemas.schedule import ScheduleResponseItem


def get_all_schedules(db: Session):
    # Hitung offset (data mulai dari baris ke-berapa)

    # Query dasar
    stmt = select(Schedule)

    # Jika ada keyword pencarian

    # Hitung total data sebelum pagination
    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))
    try:
        # Tambahkan pagination (offset + limit)
        stmt = stmt.options(joinedload(Schedule.speaker))

        # Eksekusi query dan ambil hasilnya
        results = db.scalars(stmt).all()
        results_schema = [ScheduleResponseItem.model_validate(r) for r in results]
    except Exception as e:
        print("Error in model validation:", str(e))
    # Hitung total halaman

    # Return hasil dalam bentuk dict (siap untuk API response)
    return {
        "page": 1,
        "page_size": 1,
        "count": total_count,
        "page_count": 1,
        "results": results_schema,
    }


def get_schedule_per_page_by_search(
    db: Session,
    page: int,
    page_size: int,
    search: Optional[str] = None,
):
    # Hitung offset (data mulai dari baris ke-berapa)
    offset = (page - 1) * page_size

    # Query dasar
    stmt = select(Schedule)

    # Jika ada keyword pencarian
    if search:
        stmt = stmt.where(
            Schedule.topic.ilike(f"%{search}%")  # contoh kolom tambahan
        )

    # Hitung total data sebelum pagination
    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))
    try:
        # Tambahkan pagination (offset + limit)
        stmt = (
            stmt.options(joinedload(Schedule.speaker)).offset(offset).limit(page_size)
        )

        # Eksekusi query dan ambil hasilnya
        results = db.scalars(stmt).all()
        results_schema = [ScheduleResponseItem.model_validate(r) for r in results]
    except Exception as e:
        print("Error in model validation:", str(e))
    # Hitung total halaman
    page_count = (total_count + page_size - 1) // page_size if total_count else 0

    # Return hasil dalam bentuk dict (siap untuk API response)
    return {
        "page": page,
        "page_size": page_size,
        "count": total_count,
        "page_count": page_count,
        "results": results_schema,
    }
