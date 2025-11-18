from typing import List, Optional, TypedDict
from fastapi import Query
from pydantic import BaseModel
from uuid import UUID
from schemas.user_profile import ParticipantType


class EmailWhiteListDict(TypedDict):
    emails: List[str]


class VoucherQuery(BaseModel):
    page: int = Query(1, description="Page Number")
    page_size: int = Query(10, description="Page Size")
    search: Optional[str] = Query(None, description="Search by voucher code")


class VoucherCreateRequest(BaseModel):
    code: str
    value: int = 0
    quota: int
    type: ParticipantType | None = None
    email_whitelist: EmailWhiteListDict | None = None
    is_active: bool = False


class VoucherUpdateRequest(BaseModel):
    code: str
    value: int = 0
    quota: int
    type: ParticipantType | None = None
    email_whitelist: EmailWhiteListDict | None = None
    is_active: bool = False


class VoucherUpdateStatusRequest(BaseModel):
    is_active: bool


class VoucherUpdateWhitelistRequest(BaseModel):
    email_whitelist: EmailWhiteListDict


class VoucherUpdateQuotaRequest(BaseModel):
    quota: int


class VoucherUpdateValueRequest(BaseModel):
    value: int


class VoucherUpdateTypeRequest(BaseModel):
    type: ParticipantType


class VoucherResponse(BaseModel):
    id: str
    code: str
    value: int
    type: str | None = None
    email_whitelist: EmailWhiteListDict | None = None
    quota: int
    is_active: bool


class VoucherResponseItem(BaseModel):
    id: UUID
    code: str
    value: int
    type: str | None = None
    email_whitelist: EmailWhiteListDict | None = None
    quota: int
    is_active: bool
    model_config = {"from_attributes": True}


class VoucherListResponse(BaseModel):
    page: int
    page_size: int
    count: int
    page_count: int
    results: List[VoucherResponseItem]
