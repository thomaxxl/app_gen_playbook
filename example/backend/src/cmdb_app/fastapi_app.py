from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.requests import Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from logic_bank.util import ConstraintException
from safrs.fastapi.api import SafrsFastAPI

from .bootstrap import seed_reference_data, validate_admin_schema
from .config import get_settings
from .db import (
    Base,
    attach_session_validators,
    bind_safrs_db,
    build_engine,
    build_session_factory,
    session_scope,
)
from .models import CmdbValidationError, ConfigurationItem, EXPOSED_MODELS
from .rules import activate_logic


def jsonapi_error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "jsonapi": {"version": "1.0"},
            "errors": [
                {
                    "status": str(status_code),
                    "title": "ValidationError",
                    "detail": detail,
                }
            ],
        },
    )


def create_app() -> FastAPI:
    settings = get_settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    bind_safrs_db(session_factory)
    Base.metadata.create_all(engine)
    validate_admin_schema(settings)
    attach_session_validators(
        session_factory,
        validate_required_configuration_item_references,
    )
    activate_logic(session_factory)
    with session_scope(session_factory) as session:
        seed_reference_data(session)

    app = FastAPI(
        title="CMDB Operations Console SAFRS API",
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

    @app.exception_handler(ConstraintException)
    async def handle_constraint_exception(
        _request: Request,
        exc: ConstraintException,
    ) -> JSONResponse:
        return jsonapi_error_response(400, str(exc))

    @app.exception_handler(CmdbValidationError)
    async def handle_cmdb_validation_error(
        _request: Request,
        exc: CmdbValidationError,
    ) -> JSONResponse:
        return jsonapi_error_response(400, str(exc))

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

    @app.get("/swagger.json", include_in_schema=False)
    def swagger_json() -> JSONResponse:
        return JSONResponse(app.openapi())

    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict[str, object]:
        return {"status": "ok", "framework": "fastapi"}

    @app.get("/ui/admin/admin.yaml", include_in_schema=False)
    def admin_yaml() -> FileResponse:
        return FileResponse(settings.admin_yaml_path, media_type="text/yaml")

    return app


def validate_required_configuration_item_references(
    session,
    _flush_context,
    _instances,
) -> None:
    for obj in list(session.new) + list(session.dirty):
        if not isinstance(obj, ConfigurationItem):
            continue
        if obj.service_id is None:
            raise CmdbValidationError("service_id is required")
        if obj.status_id is None:
            raise CmdbValidationError("status_id is required")
