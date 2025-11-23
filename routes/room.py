from core.log import logger
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.responses import InternalServerError, Ok, common_response
from models import get_db_sync
from repository import room as roomRepo
from schemas.common import InternalServerErrorResponse
from schemas.room import RoomDropdownResponse, RoomDropdownItem

router = APIRouter(prefix="/room", tags=["Room"])


@router.get(
    "/",
    responses={
        "200": {"model": RoomDropdownResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_room_dropdown(
    search: Optional[str] = Query(None, description="Search room by name"),
    db: Session = Depends(get_db_sync),
):
    try:
        rooms = roomRepo.get_rooms(db=db, search=search)
        room_items = [
            RoomDropdownItem(id=str(room.id), name=room.name) for room in rooms
        ]

        return common_response(Ok(data=RoomDropdownResponse(results=room_items).model_dump()))
    except Exception as e:
        logger.error(e)
        return common_response(InternalServerError(error=str(e)))
