from uuid import UUID
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from models.Stream import StreamStatus


class PlaybackURLResponse(BaseModel):
    class Playback(BaseModel):
        id: str
        url: str
        token: Optional[str]

    playback: Playback

    class Thumbnail(BaseModel):
        url: Optional[str]
        token: Optional[str]

    thumbnail: Thumbnail

    class Metadata(BaseModel):
        user_id: Optional[str]
        title: Optional[str]

    metadata: Metadata

    status: StreamStatus
    token_expires_at: Optional[datetime] = Field(
        None, description="Token expiration time for private streams"
    )


class MuxStreamDetail(BaseModel):
    id: str
    status: str
    stream_key: str
    stream_url: str

    class PlaybackIds(BaseModel):
        id: str
        policy: str

    playback_ids: List[PlaybackIds]
