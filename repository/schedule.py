from sqlalchemy.sql.operators import or_
from models.ScheduleType import ScheduleType
from typing import List
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
        stmt = stmt.where(
            Schedule.title.ilike(f"%{search}%")
        )

    if schedule_date:
        stmt = stmt.where(or_(func.date(Schedule.start) == schedule_date, func.date(Schedule.end) == schedule_date))

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
        stmt = stmt.where(
            Schedule.title.ilike(f"%{search}%")
        )

    if schedule_date:
        stmt = stmt.where(or_(func.date(Schedule.start) == schedule_date, func.date(Schedule.end) == schedule_date))

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


def create_schedule(
    db: Session,
    title: str,
    speaker_id: Union[UUID, str],
    room_id: Optional[Union[UUID, str]] = None,
    schedule_type_id: Optional[Union[UUID, str]] = None,
    description: Optional[str] = None,
    presentation_language: Optional[str] = None,
    slide_language: Optional[str] = None,
    slide_title: Optional[str] = None,
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
        slide_title=slide_title,
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
