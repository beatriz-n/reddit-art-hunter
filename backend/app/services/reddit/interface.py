from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol


@dataclass(frozen=True)
class RedditPost:
    """Minimal normalized post shape expected from an authorized Reddit source."""

    post_id: str
    subreddit: str
    title: str
    body: str
    url: str
    created_utc: datetime = field(default_factory=lambda: datetime.min.replace(tzinfo=UTC))


class RedditSource(Protocol):
    """Adapter contract for a future, authorized Reddit API integration."""

    async def fetch_recent(self, subreddit: str, limit: int = 25) -> list[RedditPost]: ...
