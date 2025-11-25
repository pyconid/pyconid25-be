from math import ceil
from sqlalchemy.sql.operators import or_
from typing import List, Tuple
from datetime import datetime, date
from typing import Optional, Union
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload
from models.Schedule import Schedule
from schemas.schedule import ScheduleResponseItem


def get_all_schedules(
    db: Session,
    search: Optional[str] = None,
    schedule_date: Optional[Union[str, date]] = None,
):
    # Hitung offset (data mulai dari baris ke-berapa)

    # Query dasar
    stmt = select(Schedule)

    # Jika ada keyword pencarian
    if search:
        stmt = stmt.where(Schedule.title.ilike(f"%{search}%"))

    if schedule_date:
        stmt = stmt.where(
            or_(
                func.date(Schedule.start) == schedule_date,
                func.date(Schedule.end) == schedule_date,
            )
        )

    # Hitung total data sebelum pagination
    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))
    results_schema = []
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
    schedule_date: Optional[Union[str, date]] = None,
):
    # Hitung offset (data mulai dari baris ke-berapa)
    offset = (page - 1) * page_size

    # Query dasar
    stmt = select(Schedule)

    # Jika ada keyword pencarian
    if search:
        stmt = stmt.where(Schedule.title.ilike(f"%{search}%"))

    if schedule_date:
        stmt = stmt.where(
            or_(
                func.date(Schedule.start) == schedule_date,
                func.date(Schedule.end) == schedule_date,
            )
        )

    # Hitung total data sebelum pagination
    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))
    results_schema = []
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


def get_schedule_cms(
    db: Session,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    search: Optional[str] = None,
    schedule_date: Optional[Union[str, date]] = None,
    all: Optional[bool] = False,
) -> Tuple[List[Schedule], int, Optional[int]]:
    num_page = None

    stmt = (
        select(Schedule)
        .options(
            joinedload(Schedule.speaker),
            joinedload(Schedule.room),
            joinedload(Schedule.schedule_type),
            joinedload(Schedule.stream),
        )
        .where(
            Schedule.deleted_at.is_(None),
        )
    )
    stmt_count = select(func.count(Schedule.id)).where(
        Schedule.deleted_at.is_(None),
    )

    if search is not None:
        search_term = Schedule.title.ilike(f"%{search}%")
        stmt = stmt.where(search_term)
        stmt_count = stmt_count.where(search_term)

    if schedule_date is not None:
        date_term = or_(
            func.date(Schedule.start) == schedule_date,
            func.date(Schedule.end) == schedule_date,
        )
        stmt = stmt.where(date_term)
        stmt_count = stmt_count.where(date_term)

    num_data = db.execute(stmt_count).scalar() or 0

    if not all and page is not None and page_size is not None:
        limit = page_size
        offset = (page - 1) * limit
        stmt = stmt.order_by(Schedule.updated_at.desc()).limit(limit).offset(offset)
        num_page = ceil(num_data / limit) if num_data > 0 else 1
    else:
        stmt = stmt.order_by(Schedule.updated_at.desc())

    results = db.execute(stmt).scalars().all()

    return results, num_data, num_page


def create_schedule(
    db: Session,
    title: str,
    speaker_id: Union[UUID, str],
    room_id: Optional[Union[UUID, str]] = None,
    schedule_type_id: Optional[Union[UUID, str]] = None,
    description: Optional[str] = None,
    presentation_language: Optional[str] = None,
    slide_language: Optional[str] = None,
    slide_link: Optional[str] = None,
    tags: Optional[List[str]] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Schedule:
    schedule = Schedule(
        title=title,
        speaker_id=speaker_id,
        room_id=room_id,
        schedule_type_id=schedule_type_id,
        description=description,
        presentation_language=presentation_language,
        slide_language=slide_language,
        slide_link=slide_link,
        tags=tags,
        start=start,
        end=end,
    )

    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return schedule


def get_schedule_by_id(
    db: Session, schedule_id: Union[UUID, str], include_deleted: bool = False
) -> Optional[Schedule]:
    stmt = (
        select(Schedule)
        .options(
            joinedload(Schedule.speaker),
            joinedload(Schedule.room),
            joinedload(Schedule.schedule_type),
        )
        .where(Schedule.id == schedule_id)
    )

    if not include_deleted:
        stmt = stmt.where(Schedule.deleted_at.is_(None))

    return db.execute(stmt).scalar_one_or_none()


def update_schedule(db: Session, schedule: Schedule, **kwargs) -> Schedule:
    for key, value in kwargs.items():
        if hasattr(schedule, key) and value is not None:
            setattr(schedule, key, value)

    schedule.updated_at = datetime.now()
    db.commit()
    db.refresh(schedule)

    return schedule


def delete_schedule(db: Session, schedule: Schedule) -> None:
    schedule.deleted_at = datetime.now()
    db.commit()
