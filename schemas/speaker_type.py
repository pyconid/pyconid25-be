from uuid import UUID
from pydantic import BaseModel


class SpeakerTypeAllResponse(BaseModel):
    class SpeakerTypeItem(BaseModel):
        id: str
        name: str

    results: list[SpeakerTypeItem]


class DetailSpeakerResponse(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}
