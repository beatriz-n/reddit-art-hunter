from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import MonitoredPost, SearchRun, Subreddit
from app.schemas.monitor import (
    MonitoredPostRead,
    MonitorStatusRead,
    SearchRunRead,
    SubredditCreate,
    SubredditRead,
)
from app.services.reddit.client import OfficialRedditSource, RedditAccessUnavailable

router = APIRouter(prefix="/monitor", tags=["subreddit monitor"])


@router.get("/status", response_model=MonitorStatusRead)
def get_status():
    settings = get_settings()
    configured = bool(settings.reddit_access_token and settings.reddit_user_agent.strip())
    approved = settings.reddit_api_approved
    return MonitorStatusRead(
        api_configured=configured,
        api_approved=approved,
        can_scan=configured and approved,
        message=(
            "API pronta para busca manual."
            if configured and approved
            else "A busca requer cadastro/acesso aprovado à Data API do Reddit e um token válido."
        ),
    )


@router.get("/subreddits", response_model=list[SubredditRead])
def list_subreddits(db: Session = Depends(get_db)):
    return db.scalars(select(Subreddit).order_by(Subreddit.priority.desc(), Subreddit.name)).all()


@router.post("/subreddits", response_model=SubredditRead, status_code=status.HTTP_201_CREATED)
def create_subreddit(payload: SubredditCreate, db: Session = Depends(get_db)):
    name = payload.name
    if db.scalar(select(Subreddit).where(Subreddit.name == name)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Essa comunidade já está cadastrada.")
    subreddit = Subreddit(**payload.model_dump(exclude={"name"}), name=name)
    db.add(subreddit)
    db.commit()
    db.refresh(subreddit)
    return subreddit


@router.delete("/subreddits/{subreddit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subreddit(subreddit_id: int, db: Session = Depends(get_db)):
    subreddit = db.get(Subreddit, subreddit_id)
    if subreddit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comunidade não encontrada.")
    db.delete(subreddit)
    db.commit()


@router.get("/posts", response_model=list[MonitoredPostRead])
def list_posts(
    subreddit_id: int | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(MonitoredPost).order_by(MonitoredPost.created_utc.desc()).limit(limit)
    if subreddit_id is not None:
        query = query.where(MonitoredPost.subreddit_id == subreddit_id)
    return db.scalars(query).all()


@router.get("/runs", response_model=list[SearchRunRead])
def list_runs(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    return db.scalars(select(SearchRun).order_by(SearchRun.started_at.desc()).limit(limit)).all()


@router.post("/subreddits/{subreddit_id}/scan", response_model=SearchRunRead)
async def scan_subreddit(subreddit_id: int, db: Session = Depends(get_db)):
    subreddit = db.get(Subreddit, subreddit_id)
    if subreddit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comunidade não encontrada.")
    run = SearchRun(subreddit_id=subreddit.id, status="blocked", message="Busca não iniciada.")
    db.add(run)
    db.flush()
    try:
        posts = await OfficialRedditSource().fetch_recent(
            subreddit.name, subreddit.max_posts_per_check
        )
        run.posts_fetched = len(posts)
        include = [word.casefold() for word in subreddit.include_keywords]
        exclude = [word.casefold() for word in subreddit.exclude_keywords]
        matched = 0
        for post in posts:
            text = f"{post.title} {post.body}".casefold()
            if (include and not any(word in text for word in include)) or any(
                word in text for word in exclude
            ):
                continue
            matched += 1
            if db.scalar(select(MonitoredPost.id).where(MonitoredPost.reddit_id == post.post_id)):
                continue
            db.add(
                MonitoredPost(
                    reddit_id=post.post_id,
                    subreddit_id=subreddit.id,
                    title=post.title,
                    body=post.body,
                    permalink=post.url,
                    created_utc=post.created_utc,
                )
            )
        run.posts_matched = matched
        run.status = "completed"
        run.message = "Consulta concluída; posts novos salvos sem dados de autor."
    except RedditAccessUnavailable as exc:
        run.status = "blocked"
        run.message = str(exc)
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        run.status = "failed"
        run.message = "A consulta à API oficial falhou. Confira acesso, limites e logs locais."
    finally:
        run.finished_at = datetime.now(UTC)
    db.commit()
    db.refresh(run)
    if run.status == "blocked":
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, run.message)
    if run.status == "failed":
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, run.message)
    return run
