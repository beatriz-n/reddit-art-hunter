import base64
from urllib.parse import urlsplit

import httpx
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.schemas.profile import ArtworkAnalysisResult, OllamaModelRead

ANALYSIS_PROMPT_VERSION = "artwork-v1"
ANALYSIS_SYSTEM_PROMPT = """You are a careful visual art cataloguer. Describe visible artistic features only.
Do not infer the artist's identity, age, gender, personality, or intent. Do not invent facts that
are not visible. Use concise tags. Return only the requested JSON object and state uncertainty
when a feature is ambiguous."""


class OllamaError(RuntimeError):
    pass


class OllamaModelNotInstalled(OllamaError):
    pass


class OllamaClient:
    """Local-only client for Ollama's generate, tags, and embed endpoints."""

    def __init__(
        self, settings: Settings | None = None, transport: httpx.AsyncBaseTransport | None = None
    ):
        self.settings = settings or get_settings()
        parsed = urlsplit(self.settings.ollama_base_url)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise OllamaError("OLLAMA_BASE_URL deve apontar para o Ollama local em localhost.")
        self.base_url = self.settings.ollama_base_url.rstrip("/")
        self.timeout = self.settings.ollama_timeout_seconds
        self.transport = transport

    async def _request_json(self, method: str, path: str, payload: dict | None = None) -> dict:
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                transport=self.transport,
                trust_env=False,
            ) as client:
                response = await client.request(method, path, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            raise OllamaError("Não foi possível conversar com o Ollama local.") from exc
        except ValueError as exc:
            raise OllamaError("O Ollama retornou uma resposta inválida.") from exc

    async def list_models(self) -> list[OllamaModelRead]:
        response = await self._request_json("GET", "/api/tags")
        result = []
        for item in response.get("models", []):
            details = item.get("details") or {}
            result.append(
                OllamaModelRead(
                    name=item.get("name") or item.get("model") or "unknown",
                    size_bytes=item.get("size"),
                    parameter_size=details.get("parameter_size"),
                    quantization=details.get("quantization_level"),
                )
            )
        return result

    async def status(self) -> dict:
        model = self.settings.ollama_model
        embedding_model = self.settings.ollama_embedding_model
        try:
            models = await self.list_models()
        except OllamaError:
            return {
                "base_url": self.base_url,
                "reachable": False,
                "model_configured": bool(model),
                "configured_model": model,
                "model_installed": False,
                "embedding_model_configured": bool(embedding_model),
                "configured_embedding_model": embedding_model,
                "embedding_model_installed": False,
                "available_models": [],
                "message": "Ollama não respondeu. Instale/inicie o Ollama e mantenha modelos escolhidos pelo usuário.",
            }
        names = {item.name for item in models}
        return {
            "base_url": self.base_url,
            "reachable": True,
            "model_configured": bool(model),
            "configured_model": model,
            "model_installed": bool(model and model in names),
            "embedding_model_configured": bool(embedding_model),
            "configured_embedding_model": embedding_model,
            "embedding_model_installed": bool(embedding_model and embedding_model in names),
            "available_models": models,
            "message": "Ollama conectado."
            if models
            else "Ollama conectado, sem modelos locais instalados.",
        }

    async def analyze_artwork(
        self, *, image: bytes, title: str, description: str
    ) -> ArtworkAnalysisResult:
        model = self.settings.ollama_model
        if not model:
            raise OllamaError("Configure OLLAMA_MODEL com um modelo multimodal já instalado.")
        models = await self.list_models()
        if model not in {item.name for item in models}:
            raise OllamaModelNotInstalled(
                f"O modelo configurado ({model}) não está instalado no Ollama."
            )
        user_prompt = (
            "Catalog this artwork for its creator's local portfolio. "
            f"Title: {title}\nArtist notes: {description or '(none)'}\n"
            "Use the image as the main evidence. Put uncertain guesses in uncertainties."
        )
        payload = {
            "model": model,
            "system": ANALYSIS_SYSTEM_PROMPT,
            "prompt": user_prompt,
            "images": [base64.b64encode(image).decode("ascii")],
            "format": ArtworkAnalysisResult.model_json_schema(),
            "stream": False,
            "options": {"temperature": 0},
        }
        response = await self._request_json("POST", "/api/generate", payload)
        try:
            return ArtworkAnalysisResult.model_validate_json(response["response"])
        except (KeyError, ValidationError, ValueError) as exc:
            raise OllamaError("A resposta do modelo não corresponde ao formato esperado.") from exc

    async def embed_text(self, text: str) -> list[float]:
        model = self.settings.ollama_embedding_model
        if not model:
            raise OllamaError(
                "Configure OLLAMA_EMBEDDING_MODEL com um modelo de embeddings já instalado."
            )
        models = await self.list_models()
        if model not in {item.name for item in models}:
            raise OllamaModelNotInstalled(
                f"O modelo de embeddings configurado ({model}) não está instalado."
            )
        response = await self._request_json(
            "POST", "/api/embed", {"model": model, "input": text, "truncate": False}
        )
        try:
            vector = response["embeddings"][0]
            if not vector or not all(isinstance(value, (int, float)) for value in vector):
                raise ValueError("Invalid embedding vector")
            return [float(value) for value in vector]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise OllamaError("O Ollama retornou um embedding inválido.") from exc


def get_ollama_client() -> OllamaClient:
    return OllamaClient()
