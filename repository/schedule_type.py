from uuid import UUID
from typing import Union
from models.ScheduleType import ScheduleType
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session


def get_all_schedule_types(db: Session) -> list[ScheduleType]:
    stmt = select(ScheduleType).order_by(ScheduleType.name.asc())
    return db.execute(stmt).scalars().all()


def get_schedule_type_by_id(db: Session, schedule_type_id: Union[UUID, str]) -> Optional[ScheduleType]:
    stmt = select(ScheduleType).where(ScheduleType.id == schedule_type_id)
    return db.execute(stmt).scalar_one_or_none()
