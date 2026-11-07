from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_reports_service_as_ready() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "reddit-art-hunter-api"}


def test_unknown_route_uses_fastapi_not_found_response() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/not-a-route")

    assert response.status_code == 404


def test_profile_api_reports_missing_database_configuration(monkeypatch) -> None:
    from types import SimpleNamespace

    import app.db.session as db_session

    db_session.get_session_factory.cache_clear()
    monkeypatch.setattr(
        db_session,
        "get_settings",
        lambda: SimpleNamespace(database_url=None),
    )
    with TestClient(app) as client:
        response = client.get("/api/v1/profile/styles")
    db_session.get_session_factory.cache_clear()

    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]
