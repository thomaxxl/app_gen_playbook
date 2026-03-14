# `backend/src/my_app/files/api.py`

See also:

- [../../../../specs/contracts/files/uploads-and-frontend-integration.md](../../../../specs/contracts/files/uploads-and-frontend-integration.md)

```python
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response

from ..db import session_scope
from .models import StoredFile
from .service import upload_content
from .storage import LocalFilesystemStorage


def build_files_router(*, session_factory, settings) -> APIRouter:
    router = APIRouter()
    storage = LocalFilesystemStorage(settings.media_root, settings.media_internal_prefix)

    @router.put("/api/stored_files/{file_id}/content")
    async def upload_stored_file_content(
        file_id: str,
        file: Annotated[UploadFile, File()],
        purpose: Annotated[str | None, Form()] = None,
    ):
        with session_scope(session_factory) as session:
            stored_file = session.get(StoredFile, file_id)
            if not stored_file:
                raise HTTPException(status_code=404, detail="Stored file not found")
            if stored_file.status not in {"pending", "failed"}:
                raise HTTPException(status_code=409, detail="Upload state not allowed")

            result = upload_content(
                session,
                storage,
                stored_file=stored_file,
                filename=file.filename or stored_file.original_filename,
                source_stream=file.file,
            )

        return JSONResponse(
            {
                "data": {
                    "type": "stored_files",
                    "id": result.stored_file.id,
                    "attributes": {
                        "original_filename": result.stored_file.original_filename,
                        "media_type": result.stored_file.media_type,
                        "media_kind": result.stored_file.media_kind,
                        "byte_size": result.stored_file.byte_size,
                        "status": result.stored_file.status,
                        "download_url": result.download_url,
                        "preview_url": result.preview_url,
                    },
                }
            }
        )

    @router.get("/media/{file_id}")
    def get_media(file_id: str):
        with session_scope(session_factory) as session:
            stored_file = session.get(StoredFile, file_id)
            if not stored_file or stored_file.status != "ready":
                raise HTTPException(status_code=404, detail="Media not found")

        if settings.media_serve_mode == "nginx":
            redirect_path = storage.internal_redirect_path(stored_file.storage_key)
            if not redirect_path:
                raise HTTPException(status_code=500, detail="Internal redirect path unavailable")
            response = Response(status_code=200)
            response.headers["X-Accel-Redirect"] = redirect_path
            response.headers["Content-Type"] = stored_file.media_type
            return response

        local_path = storage.local_path(stored_file.storage_key)
        if not local_path:
            raise HTTPException(status_code=404, detail="Media path unavailable")
        return FileResponse(local_path, media_type=stored_file.media_type)

    return router
```
