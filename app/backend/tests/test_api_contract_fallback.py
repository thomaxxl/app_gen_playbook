from pathlib import Path

import yaml

from chess_tournament import create_app
from chess_tournament.config import get_settings
from chess_tournament.db import session_scope
from chess_tournament.models import Pairing, PairingStatus, Player, Tournament


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CHESS_TOURNAMENT_DB_PATH", str(tmp_path / "fallback.sqlite"))
    monkeypatch.setenv(
        "CHESS_TOURNAMENT_ADMIN_YAML_PATH",
        str(Path(__file__).resolve().parents[2] / "reference" / "admin.yaml"),
    )


def load_admin_schema() -> dict:
    with get_settings().admin_yaml_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def endpoint_for(schema: dict, resource_key: str) -> str:
    endpoint = schema["resources"][resource_key].get("endpoint")
    assert endpoint, resource_key
    return endpoint


def test_app_builds_and_registers_core_routes(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    schema = load_admin_schema()
    route_paths = {route.path for route in app.routes}

    assert "/healthz" in route_paths
    assert "/docs" in route_paths
    assert "/jsonapi.json" in route_paths
    assert "/ui/admin/admin.yaml" in route_paths
    assert endpoint_for(schema, "Tournament") in route_paths
    assert endpoint_for(schema, "Player") in route_paths
    assert endpoint_for(schema, "Pairing") in route_paths
    assert endpoint_for(schema, "PairingStatus") in route_paths


def test_openapi_generation_works_without_http_client(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    schema = load_admin_schema()
    spec = app.openapi()

    assert "paths" in spec
    assert endpoint_for(schema, "Tournament") in spec["paths"]
    assert endpoint_for(schema, "Player") in spec["paths"]
    assert endpoint_for(schema, "Pairing") in spec["paths"]
    assert endpoint_for(schema, "PairingStatus") in spec["paths"]


def test_seed_and_rule_behavior_via_session_factory(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        assert session.query(PairingStatus).count() == 3
        assert session.query(Tournament).count() == 2
        assert session.query(Player).count() == 8
        assert session.query(Pairing).count() == 4

        pairing = session.get(Pairing, 1)
        tournament = session.query(Tournament).filter(Tournament.code == "OPEN26").one()
        assert pairing is not None
        assert pairing.status_code == "scheduled"
        assert pairing.is_reported is False
        assert tournament.player_count == 6
        assert tournament.pairing_count == 3
        assert tournament.reported_pairing_count == 1
