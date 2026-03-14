# Uploads Patch: `backend/src/my_app/fastapi_app.py`

Apply this snippet only when the uploads feature pack is enabled.

Add the import:

```python
from .files.api import build_files_router
```

Then add the router registration before `return app`:

```python
    app.include_router(build_files_router(session_factory, settings))
```

This patch is feature-owned. Do not treat the core FastAPI template as a file
to be manually uncommented.
