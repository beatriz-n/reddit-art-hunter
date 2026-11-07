from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import Artwork, ArtworkAnalysis
from app.schemas.profile import (
    ArtworkAnalysisRead,
    OllamaStatusRead,
    TextEmbeddingRead,
    TextEmbeddingRequest,
)
from app.services.ai.ollama import (
    OllamaClient,
    OllamaError,
    OllamaModelNotInstalled,
    get_ollama_client,
)

router = APIRouter(prefix="/ai", tags=["local AI"])


@router.get("/status", response_model=OllamaStatusRead)
async def get_status(client: OllamaClient = Depends(get_ollama_client)):
    return await client.status()


@router.post("/artworks/{artwork_id}/analyze", response_model=ArtworkAnalysisRead)
async def analyze_artwork(
    artwork_id: str,
    db: Session = Depends(get_db),
    client: OllamaClient = Depends(get_ollama_client),
):
    artwork = db.get(Artwork, artwork_id)
    if artwork is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arte não encontrada.")
    image_path = get_settings().data_dir / "artworks" / artwork.stored_filename
    try:
        image = image_path.read_bytes()
    except OSError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Arquivo local da arte não foi encontrado."
        ) from exc
    try:
        result = await client.analyze_artwork(
            image=image,
            title=artwork.title,
            description=artwork.description,
        )
    except OllamaModelNotInstalled as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except OllamaError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    record = ArtworkAnalysis(
        artwork_id=artwork.id,
        model=client.settings.ollama_model or "unknown",
        prompt_version="artwork-v1",
        result=result.model_dump(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/artworks/{artwork_id}/analyses", response_model=list[ArtworkAnalysisRead])
def list_artwork_analyses(artwork_id: str, db: Session = Depends(get_db)):
    if db.get(Artwork, artwork_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arte não encontrada.")
    return db.scalars(
        select(ArtworkAnalysis)
        .where(ArtworkAnalysis.artwork_id == artwork_id)
        .order_by(ArtworkAnalysis.created_at.desc())
    ).all()


@router.post("/embed", response_model=TextEmbeddingRead)
async def embed_text(
    payload: TextEmbeddingRequest,
    client: OllamaClient = Depends(get_ollama_client),
):
    try:
        vector = await client.embed_text(payload.text)
    except OllamaModelNotInstalled as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except OllamaError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return TextEmbeddingRead(
        model=client.settings.ollama_embedding_model or "unknown",
        dimensions=len(vector),
        embedding=vector,
    )
