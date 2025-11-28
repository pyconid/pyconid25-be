from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.responses import Ok, common_response
from models import get_db_sync
from schemas.common import InternalServerErrorResponse
from schemas.schedule_type import ScheduleTypeAllResponse
from repository import schedule_type as scheduleTypeRepo


router = APIRouter(prefix="/schedule-type", tags=["Schedule Type"])


@router.get(
    "/",
    responses={
        "200": {"model": ScheduleTypeAllResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_schedule_type(db: Session = Depends(get_db_sync)):
    all_schedule_types = scheduleTypeRepo.get_all_schedule_types(db=db)
    return common_response(
        Ok(
            data=ScheduleTypeAllResponse(
                results=[
                    ScheduleTypeAllResponse.ScheduleTypeItem(
                        id=str(schedule_type.id), name=schedule_type.name
                    )
                    for schedule_type in all_schedule_types
                ]
            ).model_dump()
        )
    )
