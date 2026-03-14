# `backend/src/my_app/files/service.py`

See also:

- [../../../../specs/contracts/files/uploads-and-frontend-integration.md](../../../../specs/contracts/files/uploads-and-frontend-integration.md)

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
import mimetypes

from sqlalchemy.orm import Session

from .models import StoredFile
from .storage import StorageBackend


@dataclass
class UploadResult:
    stored_file: StoredFile
    download_url: str
    preview_url: str | None = None


def _guess_media_kind(media_type: str) -> str:
    if media_type.startswith("image/"):
        return "image"
    if media_type == "application/pdf":
        return "pdf"
    return "other"


def create_pending_file(
    session: Session,
    *,
    original_filename: str,
    purpose: str | None = None,
    owner_user_id: str | None = None,
    uploaded_by_user_id: str | None = None,
) -> StoredFile:
    stored_file = StoredFile(
        id=str(uuid4()),
        storage_backend="local",
        storage_key=f"pending/{uuid4()}",
        original_filename=original_filename,
        media_type="application/octet-stream",
        media_kind="other",
        byte_size=0,
        sha256="",
        status="pending",
        purpose=purpose,
        owner_user_id=owner_user_id,
        uploaded_by_user_id=uploaded_by_user_id,
    )
    session.add(stored_file)
    session.commit()
    session.refresh(stored_file)
    return stored_file


def upload_content(
    session: Session,
    storage: StorageBackend,
    *,
    stored_file: StoredFile,
    filename: str,
    source_stream,
) -> UploadResult:
    suffix = Path(filename).suffix
    temp_object = storage.write_temp(source_stream, suffix=suffix)
    content = temp_object.path.read_bytes()
    checksum = sha256(content).hexdigest()
    media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    object_key = f"objects/{stored_file.id[:2]}/{stored_file.id}/original{suffix or ''}"

    try:
        storage.finalize(temp_object, object_key)
        stored_file.storage_key = object_key
        stored_file.original_filename = filename
        stored_file.stored_extension = suffix.lstrip(".") or None
        stored_file.media_type = media_type
        stored_file.media_kind = _guess_media_kind(media_type)
        stored_file.byte_size = len(content)
        stored_file.sha256 = checksum
        stored_file.status = "ready"
        stored_file.ready_at = datetime.utcnow()
        stored_file.failure_reason = None
        session.add(stored_file)
        session.commit()
        session.refresh(stored_file)
    except Exception as exc:
        stored_file.status = "failed"
        stored_file.failure_reason = str(exc)
        session.add(stored_file)
        session.commit()
        raise

    return UploadResult(
        stored_file=stored_file,
        download_url=f"/media/{stored_file.id}",
    )
```
