from typing import List, Optional, Union
from pydantic import BaseModel
from datetime import datetime
from models.Payment import PaymentStatus


class Ticket(BaseModel):
    id: str
    name: str


class User(BaseModel):
    id: str
    first_name: str
    last_name: str


class CreatePaymentRequest(BaseModel):
    ticket_id: str


class CreatePaymentResponse(BaseModel):
    id: str
    payment_link: str
    created_at: datetime
    amount: int
    description: Optional[str] = None
    ticket: Optional[Ticket] = None


class DetailPaymentResponse(BaseModel):
    id: str
    user: User
    payment_link: str
    status: Union[PaymentStatus, str]
    created_at: datetime
    paid_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    amount: int
    description: Optional[str] = None
    ticket: Optional[Ticket] = None


class PaymentListResponse(BaseModel):
    results: List[DetailPaymentResponse]
