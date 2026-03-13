from __future__ import annotations

from datetime import datetime

import yaml

from .config import Settings
from .models import Pairing, PairingStatus, Player, Tournament

REQUIRED_RESOURCES = {
    "Tournament": "/api/tournaments",
    "Player": "/api/players",
    "Pairing": "/api/pairings",
    "PairingStatus": "/api/pairing_statuses",
}

REQUIRED_USER_KEYS = {
    "Tournament": "code",
    "Player": "full_name",
    "Pairing": "pairing_code",
    "PairingStatus": "label",
}

REQUIRED_LABELS = {
    "Tournament": "Tournaments",
    "Player": "Players",
    "Pairing": "Pairings",
    "PairingStatus": "Pairing Statuses",
}

REQUIRED_FIELDS = {
    "Tournament": {
        "id",
        "code",
        "name",
        "city",
        "start_date",
        "end_date",
        "player_count",
        "pairing_count",
        "reported_pairing_count",
    },
    "Player": {
        "id",
        "full_name",
        "federation_id",
        "rating",
        "seed_number",
        "tournament_id",
    },
    "Pairing": {
        "id",
        "pairing_code",
        "round_number",
        "board_number",
        "scheduled_at",
        "reported_at",
        "result_summary",
        "status_code",
        "is_reported",
        "reported_value",
        "tournament_id",
        "white_player_id",
        "black_player_id",
        "status_id",
    },
    "PairingStatus": {"id", "code", "label", "is_reported"},
}

REQUIRED_TRUE_FIELDS = {
    "Tournament": {"code", "name", "city", "start_date"},
    "Player": {"full_name", "federation_id", "rating", "seed_number", "tournament_id"},
    "Pairing": {
        "round_number",
        "board_number",
        "scheduled_at",
        "tournament_id",
        "white_player_id",
        "black_player_id",
        "status_id",
    },
    "PairingStatus": {"code", "label", "is_reported"},
}

REQUIRED_REFERENCE_TARGETS = {
    "Player": {
        "tournament_id": "Tournament",
    },
    "Pairing": {
        "tournament_id": "Tournament",
        "white_player_id": "Player",
        "black_player_id": "Player",
        "status_id": "PairingStatus",
    },
}

RULE_MANAGED_READONLY_FIELDS = {
    "Tournament": {"player_count", "pairing_count", "reported_pairing_count"},
    "Pairing": {"pairing_code", "status_code", "is_reported", "reported_value"},
}

EXPECTED_RELATIONSHIP_NAMES = {
    "Tournament": {"players", "pairings"},
    "Player": {"tournament", "white_pairings", "black_pairings"},
    "Pairing": {"tournament", "white_player", "black_player", "status"},
    "PairingStatus": {"pairings"},
}

SEARCHABLE_TYPES = {"text"}


def validate_admin_schema(settings: Settings) -> dict:
    content = yaml.safe_load(settings.admin_yaml_path.read_text())
    resources = (content or {}).get("resources", {})
    for resource_name, endpoint in REQUIRED_RESOURCES.items():
        resource = resources.get(resource_name)
        if resource is None:
            raise ValueError(f"admin.yaml is missing resource {resource_name}")
        if resource.get("endpoint") != endpoint:
            raise ValueError(
                f"admin.yaml resource {resource_name} has endpoint "
                f"{resource.get('endpoint')!r}, expected {endpoint!r}"
            )
        if resource.get("label") != REQUIRED_LABELS[resource_name]:
            raise ValueError(
                f"admin.yaml resource {resource_name} has label "
                f"{resource.get('label')!r}, expected {REQUIRED_LABELS[resource_name]!r}"
            )
        if resource.get("user_key") != REQUIRED_USER_KEYS[resource_name]:
            raise ValueError(
                f"admin.yaml resource {resource_name} has user_key "
                f"{resource.get('user_key')!r}, expected "
                f"{REQUIRED_USER_KEYS[resource_name]!r}"
            )

        attributes = resource.get("attributes") or {}
        missing = sorted(REQUIRED_FIELDS[resource_name] - set(attributes))
        if missing:
            raise ValueError(
                f"admin.yaml resource {resource_name} is missing required attributes {missing!r}"
            )

        if resource.get("user_key") not in attributes:
            raise ValueError(
                f"admin.yaml resource {resource_name} user_key "
                f"{resource.get('user_key')!r} is not declared in attributes"
            )

        for field_name in REQUIRED_TRUE_FIELDS.get(resource_name, set()):
            if attributes[field_name].get("required") is not True:
                raise ValueError(
                    f"admin.yaml attribute {resource_name}.{field_name} must declare required: true"
                )

        for field_name, reference_target in REQUIRED_REFERENCE_TARGETS.get(
            resource_name,
            {},
        ).items():
            config = attributes[field_name]
            if config.get("type") != "reference":
                raise ValueError(
                    f"admin.yaml attribute {resource_name}.{field_name} must use type: reference"
                )
            if config.get("reference") != reference_target:
                raise ValueError(
                    f"admin.yaml attribute {resource_name}.{field_name} has "
                    f"reference {config.get('reference')!r}, expected {reference_target!r}"
                )

        for field_name in RULE_MANAGED_READONLY_FIELDS.get(resource_name, set()):
            config = attributes[field_name]
            if config.get("readonly") is not True:
                raise ValueError(
                    f"admin.yaml attribute {resource_name}.{field_name} must declare readonly: true"
                )

        for attribute_name, config in attributes.items():
            if not isinstance(config, dict):
                continue
            if config.get("search") is True and config.get("type") not in SEARCHABLE_TYPES:
                raise ValueError(
                    f"admin.yaml attribute {resource_name}.{attribute_name} uses "
                    f"search=true with unsupported type {config.get('type')!r}"
                )

        for group_name, group in (resource.get("tab_groups") or {}).items():
            relationships = group.get("relationships") or []
            for relationship_name in relationships:
                if relationship_name not in EXPECTED_RELATIONSHIP_NAMES.get(
                    resource_name,
                    set(),
                ):
                    raise ValueError(
                        f"admin.yaml tab_groups entry {resource_name}.{group_name} "
                        f"references unknown relationship {relationship_name!r}"
                    )

    return content


def seed_reference_data(session) -> None:
    if session.query(PairingStatus).count():
        return

    scheduled = PairingStatus(code="scheduled", label="Scheduled", is_reported=False)
    in_progress = PairingStatus(
        code="in_progress",
        label="In Progress",
        is_reported=False,
    )
    reported = PairingStatus(code="reported", label="Reported", is_reported=True)
    session.add_all([scheduled, in_progress, reported])
    session.flush()

    open_tournament = Tournament(
        code="OPEN26",
        name="Spring Open 2026",
        city="St. Louis",
        start_date=datetime(2026, 3, 13, 9, 0, 0),
        end_date=datetime(2026, 3, 15, 18, 0, 0),
    )
    junior_tournament = Tournament(
        code="JUN26",
        name="Junior Cup 2026",
        city="Chicago",
        start_date=datetime(2026, 3, 13, 10, 0, 0),
        end_date=datetime(2026, 3, 13, 17, 0, 0),
    )
    session.add_all([open_tournament, junior_tournament])
    session.flush()

    open_players = [
        Player(
            full_name="IM Sofia Alvarez",
            federation_id="US-OPEN-001",
            rating=2180,
            seed_number=1,
            tournament_id=open_tournament.id,
        ),
        Player(
            full_name="FM Liam Chen",
            federation_id="US-OPEN-002",
            rating=2112,
            seed_number=2,
            tournament_id=open_tournament.id,
        ),
        Player(
            full_name="WIM Nora Sato",
            federation_id="US-OPEN-003",
            rating=2056,
            seed_number=3,
            tournament_id=open_tournament.id,
        ),
        Player(
            full_name="Aaron Patel",
            federation_id="US-OPEN-004",
            rating=1988,
            seed_number=4,
            tournament_id=open_tournament.id,
        ),
        Player(
            full_name="Maya Johnson",
            federation_id="US-OPEN-005",
            rating=1925,
            seed_number=5,
            tournament_id=open_tournament.id,
        ),
        Player(
            full_name="Victor Ramos",
            federation_id="US-OPEN-006",
            rating=1880,
            seed_number=6,
            tournament_id=open_tournament.id,
        ),
    ]
    junior_players = [
        Player(
            full_name="Chloe Evans",
            federation_id="US-JR-001",
            rating=1670,
            seed_number=1,
            tournament_id=junior_tournament.id,
        ),
        Player(
            full_name="Daniel Brooks",
            federation_id="US-JR-002",
            rating=1612,
            seed_number=2,
            tournament_id=junior_tournament.id,
        ),
    ]
    session.add_all(open_players + junior_players)
    session.flush()

    session.add_all(
        [
            Pairing(
                round_number=1,
                board_number=1,
                scheduled_at=datetime(2026, 3, 13, 9, 0, 0),
                reported_at=None,
                result_summary=None,
                tournament_id=open_tournament.id,
                white_player_id=open_players[0].id,
                black_player_id=open_players[1].id,
                status_id=scheduled.id,
            ),
            Pairing(
                round_number=1,
                board_number=2,
                scheduled_at=datetime(2026, 3, 13, 9, 0, 0),
                reported_at=None,
                result_summary=None,
                tournament_id=open_tournament.id,
                white_player_id=open_players[2].id,
                black_player_id=open_players[3].id,
                status_id=in_progress.id,
            ),
            Pairing(
                round_number=1,
                board_number=3,
                scheduled_at=datetime(2026, 3, 13, 9, 0, 0),
                reported_at=datetime(2026, 3, 13, 11, 5, 0),
                result_summary="0-1",
                tournament_id=open_tournament.id,
                white_player_id=open_players[4].id,
                black_player_id=open_players[5].id,
                status_id=reported.id,
            ),
            Pairing(
                round_number=1,
                board_number=1,
                scheduled_at=datetime(2026, 3, 13, 10, 30, 0),
                reported_at=datetime(2026, 3, 13, 12, 10, 0),
                result_summary="1/2-1/2",
                tournament_id=junior_tournament.id,
                white_player_id=junior_players[0].id,
                black_player_id=junior_players[1].id,
                status_id=reported.id,
            ),
        ]
    )
    session.flush()
