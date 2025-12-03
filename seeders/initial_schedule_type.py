from sqlalchemy import select
from sqlalchemy.orm import Session

from models.ScheduleType import ScheduleType


def initial_schedule_type(db: Session, is_commit: bool = True):
    schedule_types = [
        ScheduleType(id="019ab02c-7f07-7b9d-b803-a003f2c307f2", name="Keynote Talk"),
        ScheduleType(id="019ab02c-9e20-79ed-bc9e-d5b8dcd70beb", name="Regular Talk"),
        ScheduleType(id="019ab02c-ba54-72e8-b8c0-540951a6dfe7", name="Short Talk"),
        ScheduleType(id="019add63-842a-7814-810b-bce18978aeb4", name="Open Session"),
        ScheduleType(id="019add63-aa2b-7cd1-9fe5-beab973b926f", name="Closed Session"),
    ]

    for schedule_type in schedule_types:
        stmt = select(ScheduleType).where(ScheduleType.id == schedule_type.id)
        existing = db.execute(stmt).scalar()
        if not existing:
            db.add(schedule_type)
        else:
            existing.name = schedule_type.name

    if is_commit:
        db.commit()
