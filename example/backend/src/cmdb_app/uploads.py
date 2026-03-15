from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MEDIA_URL_PREFIX = "/media/uploads"
CONTENT_TYPE_EXTENSIONS = {
    "image/bmp": ".bmp",
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/svg+xml": ".svg",
    "image/webp": ".webp",
}
ALLOWED_EXTENSIONS = set(CONTENT_TYPE_EXTENSIONS.values())


def slugify_filename_stem(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return normalized or "image"


def resolve_extension(upload: UploadFile) -> str:
    extension = Path(upload.filename or "").suffix.lower()
    if extension in ALLOWED_EXTENSIONS:
        return extension

    content_type = (upload.content_type or "").lower()
    inferred = CONTENT_TYPE_EXTENSIONS.get(content_type)
    if inferred:
        return inferred

    raise HTTPException(status_code=400, detail="Unsupported image format")


async def save_uploaded_image(upload: UploadFile, uploads_dir: Path) -> dict[str, object]:
    content_type = (upload.content_type or "").lower()
    if content_type and not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported")

    try:
        content = await upload.read()
    finally:
        await upload.close()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Image upload exceeds the 10 MB limit",
        )

    uploads_dir.mkdir(parents=True, exist_ok=True)
    extension = resolve_extension(upload)
    stem = slugify_filename_stem(Path(upload.filename or "image").stem)
    stored_name = f"{stem}-{uuid4().hex[:12]}{extension}"
    target_path = uploads_dir / stored_name
    target_path.write_bytes(content)

    file_size_mb = round(len(content) / (1024 * 1024), 3)
    return {
        "filename": stored_name,
        "preview_url": f"{MEDIA_URL_PREFIX}/{stored_name}",
        "file_size_mb": max(file_size_mb, 0.001),
    }
