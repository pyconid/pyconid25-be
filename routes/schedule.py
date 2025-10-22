from fastapi import APIRouter, Depends
from schemas.schedule import ScheduleQuery, ScheduleResponse
from sqlalchemy.orm import Session
from core.responses import (
    InternalServerError,
    common_response,
)
from models import get_db_sync
from schemas.common import (
    InternalServerErrorResponse,
)
from repository import schedule as scheduleRepo

router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.get(
    "/",
    responses={
        "200": {"model": ScheduleResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_schedule(
    query: ScheduleQuery = Depends(), db: Session = Depends(get_db_sync)
):
    try:
        if query.all:
            data = scheduleRepo.get_all_schedules(db=db)
        else:
            data = scheduleRepo.get_schedule_per_page_by_search(
                db=db,
                page=query.page,
                page_size=query.page_size,
                search=query.search,
            )
    except Exception as e:
        return common_response(InternalServerError(error=str(e)))
    return ScheduleResponse.model_validate(data)
