import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.api.routes.profile import get_db
from app.core.config import get_settings
from app.db.base import Base
from app.main import app


@pytest.fixture
def monitor_client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    test_sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        with test_sessions() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(
        "app.api.routes.monitor.get_settings",
        lambda: get_settings().model_copy(
            update={
                "reddit_access_token": None,
                "reddit_api_approved": False,
            }
        ),
    )
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_monitor_status_is_disabled_without_explicit_approval(monitor_client):
    status = monitor_client.get("/api/v1/monitor/status")
    assert status.status_code == 200
    assert status.json()["can_scan"] is False


def test_subreddit_registration_and_duplicate_rejection(monitor_client):
    payload = {"name": "r/artcommissions", "include_keywords": ["commission", "  "]}
    created = monitor_client.post("/api/v1/monitor/subreddits", json=payload)
    assert created.status_code == 201
    assert created.json()["name"] == "artcommissions"
    assert created.json()["include_keywords"] == ["commission"]
    assert monitor_client.post("/api/v1/monitor/subreddits", json=payload).status_code == 409


def test_scan_is_blocked_without_credentials_and_recorded(monitor_client):
    community = monitor_client.post(
        "/api/v1/monitor/subreddits", json={"name": "artcommissions"}
    ).json()
    blocked = monitor_client.post(f"/api/v1/monitor/subreddits/{community['id']}/scan")
    assert blocked.status_code == 503
    history = monitor_client.get("/api/v1/monitor/runs").json()
    assert history[0]["status"] == "blocked"


def test_subreddit_interval_has_fifteen_minute_minimum(monitor_client):
    result = monitor_client.post(
        "/api/v1/monitor/subreddits", json={"name": "art", "poll_interval_minutes": 1}
    )
    assert result.status_code == 422
