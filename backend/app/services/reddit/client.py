from datetime import UTC, datetime

import httpx

from app.core.config import get_settings
from app.services.reddit.interface import RedditPost


class RedditAccessUnavailable(RuntimeError):
    pass


class OfficialRedditSource:
    """Read-only client for Reddit's OAuth API; never falls back to scraping."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def fetch_recent(self, subreddit: str, limit: int = 25) -> list[RedditPost]:
        if not self.settings.reddit_api_approved:
            raise RedditAccessUnavailable(
                "Cadastre o aplicativo e obtenha acesso aprovado à Data API para o uso pretendido."
            )
        if not self.settings.reddit_access_token:
            raise RedditAccessUnavailable(
                "Configure REDDIT_ACCESS_TOKEN após obter acesso aprovado à API."
            )
        if not self.settings.reddit_user_agent.strip():
            raise RedditAccessUnavailable("Configure um REDDIT_USER_AGENT identificável.")
        async with httpx.AsyncClient(
            base_url="https://oauth.reddit.com",
            headers={
                "Authorization": f"Bearer {self.settings.reddit_access_token}",
                "User-Agent": self.settings.reddit_user_agent,
            },
            timeout=20,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            response = await client.get(
                f"/r/{subreddit}/new", params={"limit": min(max(limit, 1), 100)}
            )
            response.raise_for_status()
            children = response.json().get("data", {}).get("children", [])
        posts = []
        for child in children:
            data = child.get("data", {})
            created = datetime.fromtimestamp(float(data.get("created_utc", 0)), tz=UTC)
            posts.append(
                RedditPost(
                    post_id=str(data["id"]),
                    subreddit=str(data.get("subreddit", subreddit)),
                    title=str(data.get("title", ""))[:500],
                    body=str(data.get("selftext", "")),
                    url=f"https://www.reddit.com{data.get('permalink', '')}",
                    created_utc=created,
                )
            )
        return posts
