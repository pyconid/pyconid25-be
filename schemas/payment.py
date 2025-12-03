from typing import List, Optional, Union
from pydantic import BaseModel
from datetime import datetime
from models.Payment import PaymentStatus


class Ticket(BaseModel):
    id: str
    name: str
    participant_type: str


class Voucher(BaseModel):
    code: str
    value: int
    participant_type: Optional[str] = None


class VoucherInfo(BaseModel):
    value: int
    participant_type: Optional[str] = None


class User(BaseModel):
    id: str
    first_name: Optional[str]
    last_name: Optional[str]
    t_shirt_size: Optional[str]


class CreatePaymentRequest(BaseModel):
    ticket_id: str
    voucher_code: Optional[str] = None


class CreatePaymentResponse(BaseModel):
    id: str
    payment_link: Optional[str] = None
    created_at: datetime
    amount: int
    description: Optional[str] = None
    ticket: Optional[Ticket] = None
    voucher: Optional[Voucher] = None


class DetailPaymentResponse(BaseModel):
    id: str
    user: User
    payment_link: Optional[str] = None
    status: Union[PaymentStatus, str]
    created_at: datetime
    paid_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    amount: int
    description: Optional[str] = None
    ticket: Optional[Ticket] = None
    voucher: Optional[VoucherInfo] = None
    participant_type: Optional[str] = None


class PaymentListResponse(BaseModel):
    results: List[DetailPaymentResponse]


class VoucherValidateRequest(BaseModel):
    code: str


class VoucherValidateResponse(BaseModel):
    code: str
    value: int
    type: Optional[str] = None
