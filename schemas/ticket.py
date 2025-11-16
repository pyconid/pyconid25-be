from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class TicketResponse(BaseModel):
    id: str
    name: str
    price: int
    user_participant_type: str
    is_sold_out: bool
    description: str | None = None


class TicketListResponse(BaseModel):
    results: List[TicketResponse]


class MyTicketInfo(BaseModel):
    id: str
    name: str
    price: int
    participant_type: str


class MyTicketVoucher(BaseModel):
    code: str
    value: int
    participant_type: Optional[str] = None


class MyTicketPayment(BaseModel):
    id: str
    amount: int
    paid_at: Optional[datetime] = None
    voucher: Optional[MyTicketVoucher] = None


class MyTicketResponse(BaseModel):
    ticket: MyTicketInfo
    payment: MyTicketPayment
    participant_type: str
