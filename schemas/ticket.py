from typing import List
from pydantic import BaseModel


class TicketResponse(BaseModel):
    id: str
    name: str
    price: int
    user_participant_type: str
    is_sold_out: bool
    description: str | None = None


class TicketListResponse(BaseModel):
    results: List[TicketResponse]
