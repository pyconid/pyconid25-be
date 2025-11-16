from pydantic import BaseModel


class SpeakerTypeAllResponse(BaseModel):
    class SpeakerTypeItem(BaseModel):
        id: str
        name: str

    results: list[SpeakerTypeItem]
