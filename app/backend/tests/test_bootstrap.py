from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from chess_tournament import create_app
from chess_tournament.bootstrap import validate_admin_schema
from chess_tournament.config import get_settings
from chess_tournament.db import session_scope
from chess_tournament.models import (
    ChessTournamentValidationError,
    Pairing,
    PairingStatus,
    Player,
    Tournament,
)


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CHESS_TOURNAMENT_DB_PATH", str(tmp_path / "bootstrap.sqlite"))
    monkeypatch.setenv(
        "CHESS_TOURNAMENT_ADMIN_YAML_PATH",
        str(Path(__file__).resolve().parents[2] / "reference" / "admin.yaml"),
    )


def test_admin_schema_has_required_resources(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    schema = validate_admin_schema(get_settings())
    assert "Tournament" in schema["resources"]
    assert "Player" in schema["resources"]
    assert "Pairing" in schema["resources"]
    assert "PairingStatus" in schema["resources"]


def test_second_startup_does_not_duplicate_seed(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    create_app()
    app = create_app()

    session_factory = app.state.session_factory
    with session_scope(session_factory) as session:
        assert session.query(PairingStatus).count() == 3
        assert session.query(Tournament).count() == 2
        assert session.query(Player).count() == 8
        assert session.query(Pairing).count() == 4
        tournament = session.query(Tournament).filter(Tournament.code == "OPEN26").one()
        assert tournament.pairing_count == 3


def test_deleting_tournament_deletes_players_and_pairings(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        tournament = session.query(Tournament).filter(Tournament.code == "JUN26").one()
        session.delete(tournament)

    with session_scope(session_factory) as session:
        assert session.query(Tournament).count() == 1
        assert session.query(Player).count() == 6
        assert session.query(Pairing).count() == 3


def test_deleting_referenced_status_fails(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises((IntegrityError, ChessTournamentValidationError)):
        with session_scope(session_factory) as session:
            status = session.query(PairingStatus).filter(
                PairingStatus.code == "scheduled"
            ).one()
            session.delete(status)

    with session_scope(session_factory) as session:
        assert session.query(PairingStatus).count() == 3
        assert session.query(Pairing).count() == 4


def test_pairings_require_references(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises((ChessTournamentValidationError, AttributeError)):
        with session_scope(session_factory) as session:
            session.add(
                Pairing(
                    round_number=2,
                    board_number=1,
                    scheduled_at=datetime(2026, 3, 13, 13, 30, 0),
                    reported_at=None,
                    result_summary=None,
                    tournament_id=None,
                    white_player_id=None,
                    black_player_id=None,
                    status_id=None,
                )
            )


def test_pairing_update_rejects_null_required_foreign_key(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises(ChessTournamentValidationError):
        with session_scope(session_factory) as session:
            pairing = session.get(Pairing, 1)
            assert pairing is not None
            pairing.status_id = None


def test_pairing_rejects_same_player_on_both_sides(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises(ChessTournamentValidationError):
        with session_scope(session_factory) as session:
            pairing = session.get(Pairing, 1)
            assert pairing is not None
            pairing.black_player_id = pairing.white_player_id
