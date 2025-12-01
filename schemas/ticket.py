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


class UserInfo(BaseModel):
    id: str
    first_name: Optional[str]
    last_name: Optional[str]
    t_shirt_size: Optional[str]


class MyTicketInfo(BaseModel):
    id: str
    name: str
    price: int
    participant_type: str


class MyTicketVoucher(BaseModel):
    value: int
    participant_type: Optional[str] = None


class MyTicketPayment(BaseModel):
    id: str
    amount: int
    paid_at: Optional[datetime] = None
    voucher: Optional[MyTicketVoucher] = None


class MyTicket(BaseModel):
    ticket: MyTicketInfo
    payment: MyTicketPayment
    participant_type: str
    user: UserInfo


class MyTicketResponse(BaseModel):
    data: Optional[MyTicket] = None
    message: str
