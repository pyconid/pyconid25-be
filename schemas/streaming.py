from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from models.StreamAsset import StreamStatus


class CreateLiveStreamRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    is_public: bool = Field(default=True, description="Public or private stream")
    schedule_id: Optional[UUID] = Field(None, description="Related schedule ID")


class UploadVideoRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    is_public: bool = Field(default=True)
    schedule_id: Optional[UUID] = None


class TrackViewRequest(BaseModel):
    started_at: datetime
    duration_watched: int = Field(..., ge=0, description="Duration watched in seconds")


class GetPlaybackURLRequest(BaseModel):
    token: Optional[str] = Field(
        None, description="Optional token for accessing shared private streams"
    )


class LiveStreamResponse(BaseModel):
    stream_id: str
    mux_stream_key: str
    mux_stream_url: str
    playback_url: Optional[str]
    status: StreamStatus


class UploadVideoResponse(BaseModel):
    stream_id: str
    mux_asset_id: str
    status: StreamStatus


class PlaybackURLResponse(BaseModel):
    playback_url: str
    thumbnail_url: Optional[str]
    is_live: bool
    status: StreamStatus
    token_expires_at: Optional[datetime] = Field(
        None, description="Token expiration time for private streams"
    )


class StreamStatusResponse(BaseModel):
    message: str
    duration: Optional[int] = Field(None, description="Stream duration in seconds")
    max_viewers: Optional[int] = Field(None, description="Max concurrent viewers")


class StreamAnalyticsResponse(BaseModel):
    total_views: int
    unique_viewers: int
    max_concurrent_viewers: int
    average_watch_time: int = Field(..., description="Average watch time in seconds")
    total_watch_time: int = Field(..., description="Total watch time in seconds")
    views_by_date: list[dict]


class StreamAssetDetail(BaseModel):
    id: str
    schedule_id: Optional[str]
    title: str
    description: Optional[str]
    is_public: bool
    is_live: bool
    status: StreamStatus
    duration: Optional[int]
    thumbnail_url: Optional[str]
    view_count: int
    max_concurrent_viewers: int
    stream_started_at: Optional[datetime]
    stream_ended_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class StreamAssetListItem(BaseModel):
    id: str
    title: str
    is_public: bool
    is_live: bool
    status: StreamStatus
    thumbnail_url: Optional[str]
    view_count: int
    duration: Optional[int]
    stream_started_at: Optional[datetime]
    created_at: datetime


class PaginatedStreamListResponse(BaseModel):
    page: int
    page_size: int
    count: int
    page_count: int
    results: List[StreamAssetListItem]


class StreamViewDetail(BaseModel):
    id: str
    stream_asset_id: str
    user_id: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_watched: int
