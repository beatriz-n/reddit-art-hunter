from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StyleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    kind: Literal["style", "category", "theme"]


class StyleRead(StyleCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ArtworkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str
    original_filename: str
    mime_type: str
    byte_size: int
    created_at: datetime
    styles: list[StyleRead]
    image_url: str


class ArtworkUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    style_ids: list[int] | None = None


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=4000)
    price_min: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    price_max: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3, pattern="^[A-Za-z]{3}$")
    active: bool = True

    @model_validator(mode="after")
    def validate_price_range(self):
        if self.price_max < self.price_min:
            raise ValueError("price_max deve ser maior ou igual a price_min")
        self.currency = self.currency.upper()
        return self


class ServiceRead(ServiceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class ArtworkAnalysisResult(BaseModel):
    visual_description: str = Field(min_length=1, max_length=1200)
    styles: list[str] = Field(max_length=12)
    themes: list[str] = Field(max_length=12)
    subjects: list[str] = Field(max_length=12)
    composition: str = Field(max_length=600)
    color_palette: list[str] = Field(max_length=10)
    complexity: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0, le=1)
    uncertainties: list[str] = Field(max_length=8)


class ArtworkAnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    artwork_id: str
    model: str
    prompt_version: str
    result: ArtworkAnalysisResult
    created_at: datetime


class OllamaModelRead(BaseModel):
    name: str
    size_bytes: int | None = None
    parameter_size: str | None = None
    quantization: str | None = None


class OllamaStatusRead(BaseModel):
    base_url: str
    reachable: bool
    model_configured: bool
    configured_model: str | None
    model_installed: bool
    embedding_model_configured: bool
    configured_embedding_model: str | None
    embedding_model_installed: bool
    available_models: list[OllamaModelRead]
    message: str


class TextEmbeddingRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


class TextEmbeddingRead(BaseModel):
    model: str
    dimensions: int
    embedding: list[float]
