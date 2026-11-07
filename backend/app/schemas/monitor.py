from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SubredditCreate(BaseModel):
    name: str = Field(min_length=2, max_length=82, pattern=r"^(r/)?[A-Za-z0-9_]+$")
    active: bool = True
    priority: int = Field(default=0, ge=0, le=10)
    poll_interval_minutes: int = Field(default=60, ge=15, le=10080)
    max_posts_per_check: int = Field(default=25, ge=1, le=100)
    include_keywords: list[str] = Field(default_factory=list, max_length=30)
    exclude_keywords: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip().removeprefix("r/")

    @field_validator("include_keywords", "exclude_keywords")
    @classmethod
    def normalize_keywords(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(item.strip() for item in values if item.strip()))


class SubredditRead(SubredditCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class MonitoredPostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reddit_id: str
    subreddit_id: int
    title: str
    body: str
    permalink: str
    created_utc: datetime
    fetched_at: datetime


class SearchRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subreddit_id: int
    status: str
    posts_fetched: int
    posts_matched: int
    message: str
    started_at: datetime
    finished_at: datetime | None


class MonitorStatusRead(BaseModel):
    api_configured: bool
    api_approved: bool
    can_scan: bool
    message: str
