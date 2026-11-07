from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.routes.ai as ai_routes
import app.models
from app.api.routes.ai import get_ollama_client
from app.api.routes.profile import get_db
from app.db.base import Base
from app.main import app
from app.schemas.profile import ArtworkAnalysisResult
from app.services import artwork_storage


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        with test_sessions() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_profile_api_creates_and_lists_classifications(client: TestClient) -> None:
    created = client.post("/api/v1/profile/styles", json={"name": "Dark art", "kind": "style"})

    assert created.status_code == 201
    assert created.json()["name"] == "Dark art"
    assert client.get("/api/v1/profile/styles").json() == [created.json()]


def test_profile_api_rejects_duplicate_classification_names(client: TestClient) -> None:
    payload = {"name": "Semi-realista", "kind": "style"}
    assert client.post("/api/v1/profile/styles", json=payload).status_code == 201

    duplicate = client.post("/api/v1/profile/styles", json=payload)

    assert duplicate.status_code == 409


def test_profile_api_creates_service_with_currency_normalized(client: TestClient) -> None:
    response = client.post(
        "/api/v1/profile/services",
        json={
            "name": "Retrato",
            "description": "Arte digital colorida",
            "price_min": "30.00",
            "price_max": "120.00",
            "currency": "brl",
            "active": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["currency"] == "BRL"
    assert response.json()["price_min"] == "30.00"


def test_local_ai_status_reports_runtime_and_installed_models(client: TestClient) -> None:
    class FakeOllama:
        async def status(self):
            return {
                "base_url": "http://localhost:11434",
                "reachable": True,
                "model_configured": True,
                "configured_model": "vision:latest",
                "model_installed": True,
                "embedding_model_configured": False,
                "configured_embedding_model": None,
                "embedding_model_installed": False,
                "available_models": [{"name": "vision:latest"}],
                "message": "Ollama conectado.",
            }

    app.dependency_overrides[get_ollama_client] = FakeOllama
    response = client.get("/api/v1/ai/status")

    assert response.status_code == 200
    assert response.json()["model_installed"] is True


def test_local_ai_analyzes_and_persists_portfolio_artwork(
    client: TestClient, tmp_path, monkeypatch
) -> None:
    data_dir = tmp_path
    local_settings = SimpleNamespace(data_dir=data_dir)
    monkeypatch.setattr(artwork_storage, "get_settings", lambda: local_settings)
    monkeypatch.setattr(ai_routes, "get_settings", lambda: local_settings)

    class FakeOllama:
        settings = SimpleNamespace(ollama_model="vision:latest")

        async def analyze_artwork(self, *, image, title, description):
            assert image.startswith(b"\x89PNG")
            assert title == "Dark portrait"
            return ArtworkAnalysisResult(
                visual_description="A dark fantasy character portrait.",
                styles=["semi-realistic"],
                themes=["dark fantasy"],
                subjects=["portrait"],
                composition="Centered bust portrait.",
                color_palette=["black", "violet"],
                complexity=3,
                confidence=0.9,
                uncertainties=[],
            )

    app.dependency_overrides[get_ollama_client] = FakeOllama
    image_data = BytesIO()
    Image.new("RGB", (3, 3), "purple").save(image_data, format="PNG")
    image_data.seek(0)
    created = client.post(
        "/api/v1/profile/artworks",
        data={"title": "Dark portrait", "description": "Original character"},
        files={"image": ("portrait.png", image_data, "image/png")},
    )
    assert created.status_code == 201

    analyzed = client.post(f"/api/v1/ai/artworks/{created.json()['id']}/analyze")

    assert analyzed.status_code == 200
    assert analyzed.json()["model"] == "vision:latest"
    assert analyzed.json()["result"]["themes"] == ["dark fantasy"]
    history = client.get(f"/api/v1/ai/artworks/{created.json()['id']}/analyses")
    assert len(history.json()) == 1
