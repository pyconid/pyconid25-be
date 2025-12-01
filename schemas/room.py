from pydantic import BaseModel
from typing import List


class RoomDropdownItem(BaseModel):
    id: str
    name: str


class RoomDropdownResponse(BaseModel):
    results: List[RoomDropdownItem]
