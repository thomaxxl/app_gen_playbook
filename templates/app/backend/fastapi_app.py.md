from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.requests import Request
from fastapi.responses import FileResponse, RedirectResponse
from safrs.fastapi.api import SafrsFastAPI

from .bootstrap import validate_admin_schema, validate_observer_database
from .config import get_settings
from .db import bind_safrs_db, build_engine, build_session_factory
from .models import EXPOSED_MODELS


def _configure_read_only_models() -> None:
    for model in EXPOSED_MODELS:
        model.http_methods = ["GET"]


def create_app() -> FastAPI:
    settings = get_settings()
    engine = build_engine(settings.database_url)
    validate_observer_database(engine)
    session_factory = build_session_factory(engine)
    bind_safrs_db(session_factory)
    validate_admin_schema(settings)

    app = FastAPI(
        title="Run Observer API",
        docs_url=None,
        redoc_url=None,
        openapi_url="/jsonapi.json",
    )

    @app.middleware("http")
    async def cleanup_session(request: Request, call_next):  # noqa: ARG001
        try:
            return await call_next(request)
        finally:
            session_factory.remove()

    @app.get("/docs", include_in_schema=False)
    def docs():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url or "/jsonapi.json",
            title=f"{app.title} - Swagger UI",
            swagger_ui_parameters=app.swagger_ui_parameters,
        )

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs", status_code=307)

    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict[str, object]:
        return {
            "status": "ok",
            "database": str(settings.db_path),
            "framework": "fastapi+safrs",
            "mode": "run-observer",
        }

    @app.get("/ui/admin/admin.yaml", include_in_schema=False)
    def admin_yaml() -> FileResponse:
        return FileResponse(settings.admin_yaml_path, media_type="text/yaml")

    @app.get("/swagger.json", include_in_schema=False)
    def swagger_json() -> dict[str, object]:
        return app.openapi()

    api = SafrsFastAPI(app, prefix=settings.api_prefix)
    app.state.safrs_api = api
    app.state.engine = engine
    app.state.session_factory = session_factory

    _configure_read_only_models()

    for model in EXPOSED_MODELS:
        api.expose_object(model)

    return app
