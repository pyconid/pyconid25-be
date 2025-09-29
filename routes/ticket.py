from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from models import get_db_sync
from repository.ticket import get_active_tickets
from schemas.ticket import TicketResponse

router = APIRouter(prefix="/ticket", tags=["Ticket"])


class TicketListResponse(BaseModel):
    results: List[TicketResponse]


@router.get("/", response_model=TicketListResponse)
def list_ticket(db: Session = Depends(get_db_sync)):
    try:
        tickets = get_active_tickets(db)
        results = [
            TicketResponse(
                id=str(t.id),
                name=t.name,
                price=t.price,
                user_participant_type=t.user_participant_type,
                is_sold_out=t.is_sold_out,
                description=t.description,
            )
            for t in tickets
        ]
        return TicketListResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
