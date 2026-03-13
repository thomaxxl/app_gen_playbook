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
from .models import (
    ChessTournamentValidationError,
    EXPOSED_MODELS,
    Pairing,
    Player,
)
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
    attach_session_validators(session_factory, validate_pairing_consistency)
    activate_logic(session_factory)
    with session_scope(session_factory) as session:
        seed_reference_data(session)

    app = FastAPI(
        title="Chess Tournament Management SAFRS API",
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

    @app.exception_handler(ChessTournamentValidationError)
    async def handle_chess_tournament_validation_error(
        _request: Request,
        exc: ChessTournamentValidationError,
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


def validate_pairing_consistency(session, _flush_context, _instances) -> None:
    for obj in list(session.new) + list(session.dirty):
        if isinstance(obj, Player) and obj.tournament_id is None:
            raise ChessTournamentValidationError("tournament_id is required")

        if not isinstance(obj, Pairing):
            continue

        if obj.tournament_id is None:
            raise ChessTournamentValidationError("tournament_id is required")
        if obj.white_player_id is None:
            raise ChessTournamentValidationError("white_player_id is required")
        if obj.black_player_id is None:
            raise ChessTournamentValidationError("black_player_id is required")
        if obj.status_id is None:
            raise ChessTournamentValidationError("status_id is required")
        if obj.white_player_id == obj.black_player_id:
            raise ChessTournamentValidationError(
                "white_player_id and black_player_id must differ"
            )

        white_player = session.get(Player, obj.white_player_id)
        black_player = session.get(Player, obj.black_player_id)

        if white_player is None:
            raise ChessTournamentValidationError("white_player_id must reference a player")
        if black_player is None:
            raise ChessTournamentValidationError("black_player_id must reference a player")
        if white_player.tournament_id != obj.tournament_id:
            raise ChessTournamentValidationError(
                "white_player_id must belong to the selected tournament"
            )
        if black_player.tournament_id != obj.tournament_id:
            raise ChessTournamentValidationError(
                "black_player_id must belong to the selected tournament"
            )
