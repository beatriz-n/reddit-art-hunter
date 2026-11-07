from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings

MAX_IMAGE_BYTES = 15 * 1024 * 1024
IMAGE_FORMATS = {
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    ".webp": ("image/webp", b"RIFF"),
    ".gif": ("image/gif", (b"GIF87a", b"GIF89a")),
}


async def save_artwork_image(upload: UploadFile) -> tuple[str, str, int]:
    original_name = Path(upload.filename or "artwork").name[:255]
    extension = Path(original_name).suffix.lower()
    expected = IMAGE_FORMATS.get(extension)
    if not expected:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Formato permitido: PNG, JPG, WEBP ou GIF."
        )
    content = await upload.read(MAX_IMAGE_BYTES + 1)
    if not content or len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "A imagem deve ter até 15 MB."
        )
    mime_type, signature = expected
    signatures = signature if isinstance(signature, tuple) else (signature,)
    if not any(content.startswith(prefix) for prefix in signatures):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "O conteúdo não corresponde ao formato da imagem.",
        )
    if upload.content_type and upload.content_type not in (mime_type, "application/octet-stream"):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "O tipo MIME não corresponde à extensão."
        )
    try:
        with Image.open(BytesIO(content)) as image:
            if image.width * image.height > 50_000_000:
                raise HTTPException(
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "A imagem excede 50 megapixels."
                )
            expected_format = {
                ".png": "PNG",
                ".jpg": "JPEG",
                ".jpeg": "JPEG",
                ".webp": "WEBP",
                ".gif": "GIF",
            }[extension]
            if image.format != expected_format:
                raise HTTPException(
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    "O formato interno não corresponde à extensão.",
                )
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "O arquivo não é uma imagem válida."
        ) from exc
    except Image.DecompressionBombError as exc:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "A imagem excede o limite de dimensões."
        ) from exc

    directory = get_settings().data_dir / "artworks"
    directory.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{extension}"
    (directory / stored_name).write_bytes(content)
    return stored_name, mime_type, len(content)


def remove_artwork_image(stored_name: str) -> None:
    directory = (get_settings().data_dir / "artworks").resolve()
    candidate = (directory / stored_name).resolve()
    if candidate.parent == directory and candidate.is_file():
        candidate.unlink()
