from uuid import UUID
from pydantic import BaseModel


class ScheduleTypeAllResponse(BaseModel):
    class ScheduleTypeItem(BaseModel):
        id: str
        name: str

    results: list[ScheduleTypeItem]


class DetailScheduleTypeResponse(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}
