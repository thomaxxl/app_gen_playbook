# `backend/src/my_app/fastapi_app.py`

See also:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/rules/README.md](../../../specs/contracts/rules/README.md)
- [../../../specs/contracts/backend/runtime-and-startup.md](../../../specs/contracts/backend/runtime-and-startup.md)
- [../../../specs/contracts/backend/bootstrap-and-db-lifecycle.md](../../../specs/contracts/backend/bootstrap-and-db-lifecycle.md)
- [../../../specs/contracts/rules/lifecycle.md](../../../specs/contracts/rules/lifecycle.md)

This is the core FastAPI app shape used by the current validation apps.

```python
from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, RedirectResponse
from safrs.fastapi.api import SafrsFastAPI

from .bootstrap import seed_reference_data, validate_admin_schema
from .config import get_settings
from .db import (
    Base,
    bind_safrs_db,
    build_engine,
    build_session_factory,
    session_scope,
)
from .models import EXPOSED_MODELS
from .rules import activate_logic


def create_app() -> FastAPI:
    settings = get_settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    bind_safrs_db(session_factory)
    Base.metadata.create_all(engine)
    validate_admin_schema(settings)
    activate_logic(session_factory)
    with session_scope(session_factory) as session:
        seed_reference_data(session)

    app = FastAPI(
        title="My App SAFRS API",
        docs_url=None,
        redoc_url=None,
        openapi_url="/jsonapi.json",
    )

    @app.middleware("http")
    async def cleanup_session(request, call_next):
        try:
            return await call_next(request)
        finally:
            session_factory.remove()

    api = SafrsFastAPI(app, prefix=settings.api_prefix)
    app.state.safrs_api = api
    app.state.engine = engine
    app.state.session_factory = session_factory

    for model in EXPOSED_MODELS:
        api.expose_object(model)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs", status_code=307)

    @app.get("/docs", include_in_schema=False)
    def docs():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url or "/jsonapi.json",
            title=f"{app.title} - Swagger UI",
            swagger_ui_parameters=app.swagger_ui_parameters,
        )

    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict[str, object]:
        return {"status": "ok", "framework": "fastapi"}

    @app.get("/ui/admin/admin.yaml", include_in_schema=False)
    def admin_yaml() -> FileResponse:
        return FileResponse(settings.admin_yaml_path, media_type="text/yaml")

    return app
```

Notes:

- Keep `/jsonapi.json` canonical for FastAPI SAFRS.
- Serve `admin.yaml` from the backend so the frontend can stay same-origin.
- Put the root redirect on `/docs`, not a JSON metadata response.
- Activate LogicBank against the real app session factory before seed/bootstrap.
- Perform `admin.yaml` validation and idempotent seed/bootstrap before exposing
  SAFRS routes.
