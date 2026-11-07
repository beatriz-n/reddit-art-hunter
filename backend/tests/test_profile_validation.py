import asyncio
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.datastructures import UploadFile
from PIL import Image
from pydantic import ValidationError
from starlette.datastructures import Headers

from app.schemas.profile import ServiceCreate, StyleCreate
from app.services import artwork_storage


def test_service_price_range_must_be_ordered() -> None:
    with pytest.raises(ValidationError):
        ServiceCreate(name="Portrait", price_min="100", price_max="50")


def test_service_currency_is_normalized() -> None:
    service = ServiceCreate(name="Portrait", price_min="20", price_max="80", currency="brl")
    assert service.currency == "BRL"


def test_style_kind_is_restricted_to_supported_types() -> None:
    with pytest.raises(ValidationError):
        StyleCreate(name="Painterly", kind="invalid")


def test_artwork_upload_accepts_and_stores_a_valid_png(tmp_path, monkeypatch) -> None:
    image_bytes = BytesIO()
    Image.new("RGB", (2, 2), color="purple").save(image_bytes, format="PNG")
    image_bytes.seek(0)
    upload = UploadFile(
        filename="reference.png",
        file=image_bytes,
        headers=Headers({"content-type": "image/png"}),
    )
    monkeypatch.setattr(artwork_storage, "get_settings", lambda: SimpleNamespace(data_dir=tmp_path))

    stored_name, mime_type, size = asyncio.run(artwork_storage.save_artwork_image(upload))

    assert mime_type == "image/png"
    assert size == image_bytes.tell()
    assert (tmp_path / "artworks" / stored_name).is_file()


def test_artwork_upload_rejects_mismatched_image_content() -> None:
    upload = UploadFile(
        filename="not-an-image.jpg",
        file=BytesIO(b"not a jpeg"),
        headers=Headers({"content-type": "image/jpeg"}),
    )
    with pytest.raises(HTTPException) as error:
        asyncio.run(artwork_storage.save_artwork_image(upload))
    assert error.value.status_code == 415
