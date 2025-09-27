from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import get_db_sync
from repository.ticket import get_active_tickets
from schemas.ticket import TicketResponse

router = APIRouter(prefix="/ticket", tags=["Ticket"])


@router.get("/", response_model=dict)
def list_ticket(db: Session = Depends(get_db_sync)):
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
    return {"results": results}
