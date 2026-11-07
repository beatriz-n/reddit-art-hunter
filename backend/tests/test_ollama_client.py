import asyncio
import base64
import json
from types import SimpleNamespace

import pytest

from app.services.ai.ollama import OllamaClient, OllamaError, OllamaModelNotInstalled


def settings(**overrides):
    values = {
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "vision:latest",
        "ollama_embedding_model": "embed:latest",
        "ollama_timeout_seconds": 20,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_ollama_client_refuses_non_local_urls() -> None:
    with pytest.raises(OllamaError, match="local"):
        OllamaClient(settings(ollama_base_url="https://example.com"))


def test_art_analysis_uses_an_installed_model_and_validates_structured_json() -> None:
    client = OllamaClient(settings())
    calls = []
    expected = {
        "visual_description": "A dark fantasy portrait with dramatic rim lighting.",
        "styles": ["semi-realistic"],
        "themes": ["dark fantasy"],
        "subjects": ["portrait"],
        "composition": "Centered bust portrait.",
        "color_palette": ["black", "violet"],
        "complexity": 3,
        "confidence": 0.88,
        "uncertainties": [],
    }

    async def request(method, path, payload=None):
        calls.append((method, path, payload))
        if path == "/api/tags":
            return {"models": [{"name": "vision:latest"}]}
        return {"response": json.dumps(expected)}

    client._request_json = request
    result = asyncio.run(
        client.analyze_artwork(image=b"local-image", title="Vampire", description="OC art")
    )

    assert result.visual_description == expected["visual_description"]
    generation = calls[1][2]
    assert generation["model"] == "vision:latest"
    assert generation["stream"] is False
    assert generation["images"] == [base64.b64encode(b"local-image").decode("ascii")]
    assert "required" in generation["format"]


def test_art_analysis_never_pulls_a_model_that_is_not_installed() -> None:
    client = OllamaClient(settings())

    async def request(method, path, payload=None):
        return {"models": [{"name": "some-other-model"}]}

    client._request_json = request
    with pytest.raises(OllamaModelNotInstalled):
        asyncio.run(client.analyze_artwork(image=b"x", title="test", description=""))


def test_text_embedding_returns_a_numeric_vector_from_local_model() -> None:
    client = OllamaClient(settings())
    calls = []

    async def request(method, path, payload=None):
        calls.append((method, path, payload))
        if path == "/api/tags":
            return {"models": [{"name": "embed:latest"}]}
        return {"embeddings": [[0.25, -0.5, 0.75]]}

    client._request_json = request
    vector = asyncio.run(client.embed_text("dark fantasy portrait"))

    assert vector == [0.25, -0.5, 0.75]
    assert calls[1][2] == {
        "model": "embed:latest",
        "input": "dark fantasy portrait",
        "truncate": False,
    }
