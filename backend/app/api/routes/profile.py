import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import ArtStyle, Artwork, CommissionService
from app.schemas.profile import (
    ArtworkRead,
    ArtworkUpdate,
    ServiceCreate,
    ServiceRead,
    StyleCreate,
    StyleRead,
)
from app.services.artwork_storage import remove_artwork_image, save_artwork_image

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profile", tags=["art profile"])


def artwork_response(artwork: Artwork) -> ArtworkRead:
    return ArtworkRead(
        id=artwork.id,
        title=artwork.title,
        description=artwork.description,
        original_filename=artwork.original_filename,
        mime_type=artwork.mime_type,
        byte_size=artwork.byte_size,
        created_at=artwork.created_at,
        styles=artwork.styles,
        image_url=f"/media/artworks/{artwork.stored_filename}",
    )


@router.get("/artworks", response_model=list[ArtworkRead])
def list_artworks(db: Session = Depends(get_db)):
    records = db.scalars(
        select(Artwork).options(selectinload(Artwork.styles)).order_by(Artwork.created_at.desc())
    ).all()
    return [artwork_response(record) for record in records]


@router.post("/artworks", response_model=ArtworkRead, status_code=status.HTTP_201_CREATED)
async def create_artwork(
    image: UploadFile = File(...),
    title: str = Form(min_length=1, max_length=160),
    description: str = Form(default="", max_length=4000),
    style_ids: list[int] = Form(default=[]),
    db: Session = Depends(get_db),
):
    stored_name, mime_type, byte_size = await save_artwork_image(image)
    try:
        styles = (
            db.scalars(select(ArtStyle).where(ArtStyle.id.in_(style_ids))).all()
            if style_ids
            else []
        )
        if len(styles) != len(set(style_ids)):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "Uma ou mais classificações não existem."
            )
        artwork = Artwork(
            id=str(uuid4()),
            title=title.strip(),
            description=description.strip(),
            original_filename=Path(image.filename or "artwork").name[:255],
            stored_filename=stored_name,
            mime_type=mime_type,
            byte_size=byte_size,
            styles=styles,
        )
        db.add(artwork)
        db.commit()
        db.refresh(artwork)
        return artwork_response(artwork)
    except Exception:
        db.rollback()
        remove_artwork_image(stored_name)
        raise


@router.patch("/artworks/{artwork_id}", response_model=ArtworkRead)
def update_artwork(artwork_id: str, payload: ArtworkUpdate, db: Session = Depends(get_db)):
    artwork = db.scalar(
        select(Artwork).options(selectinload(Artwork.styles)).where(Artwork.id == artwork_id)
    )
    if not artwork:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arte não encontrada.")
    values = payload.model_dump(exclude_unset=True)
    if "style_ids" in values:
        ids = values.pop("style_ids") or []
        styles = db.scalars(select(ArtStyle).where(ArtStyle.id.in_(ids))).all() if ids else []
        if len(styles) != len(set(ids)):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "Uma ou mais classificações não existem."
            )
        artwork.styles = styles
    for field, value in values.items():
        if value is not None:
            setattr(artwork, field, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(artwork)
    return artwork_response(artwork)


@router.delete("/artworks/{artwork_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artwork(artwork_id: str, db: Session = Depends(get_db)):
    artwork = db.get(Artwork, artwork_id)
    if not artwork:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arte não encontrada.")
    stored_name = artwork.stored_filename
    db.delete(artwork)
    db.commit()
    remove_artwork_image(stored_name)


@router.get("/styles", response_model=list[StyleRead])
def list_styles(db: Session = Depends(get_db)):
    return db.scalars(select(ArtStyle).order_by(ArtStyle.kind, ArtStyle.name)).all()


@router.post("/styles", response_model=StyleRead, status_code=status.HTTP_201_CREATED)
def create_style(payload: StyleCreate, db: Session = Depends(get_db)):
    record = ArtStyle(name=payload.name.strip(), kind=payload.kind)
    db.add(record)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Já existe uma classificação com esse nome."
        ) from exc
    db.refresh(record)
    return record


@router.delete("/styles/{style_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_style(style_id: int, db: Session = Depends(get_db)):
    record = db.get(ArtStyle, style_id)
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Classificação não encontrada.")
    db.delete(record)
    db.commit()


@router.get("/services", response_model=list[ServiceRead])
def list_services(db: Session = Depends(get_db)):
    return db.scalars(select(CommissionService).order_by(CommissionService.created_at.desc())).all()


@router.post("/services", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)):
    record = CommissionService(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/services/{service_id}", response_model=ServiceRead)
def update_service(service_id: int, payload: ServiceCreate, db: Session = Depends(get_db)):
    record = db.get(CommissionService, service_id)
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Serviço não encontrado.")
    for field, value in payload.model_dump().items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, db: Session = Depends(get_db)):
    record = db.get(CommissionService, service_id)
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Serviço não encontrado.")
    db.delete(record)
    db.commit()
