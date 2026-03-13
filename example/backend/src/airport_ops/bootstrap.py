from __future__ import annotations

from datetime import datetime

import yaml

from .config import Settings
from .models import Flight, FlightStatus, Gate

REQUIRED_RESOURCES = {
    "Gate": "/api/gates",
    "Flight": "/api/flights",
    "FlightStatus": "/api/flight_statuses",
}

REQUIRED_USER_KEYS = {
    "Gate": "code",
    "Flight": "flight_number",
    "FlightStatus": "label",
}

REQUIRED_LABELS = {
    "Gate": "Gates",
    "Flight": "Flights",
    "FlightStatus": "Flight Statuses",
}

REQUIRED_FIELDS = {
    "Gate": {"id", "code", "terminal", "flight_count", "total_delay_minutes"},
    "Flight": {
        "id",
        "flight_number",
        "destination",
        "scheduled_departure",
        "actual_departure",
        "delay_minutes",
        "gate_id",
        "status_id",
        "status_code",
        "is_departed",
    },
    "FlightStatus": {"id", "code", "label", "is_departed"},
}

REQUIRED_TRUE_FIELDS = {
    "Gate": {"code", "terminal"},
    "Flight": {
        "flight_number",
        "destination",
        "scheduled_departure",
        "delay_minutes",
        "gate_id",
        "status_id",
    },
    "FlightStatus": {"code", "label", "is_departed"},
}

REQUIRED_REFERENCE_TARGETS = {
    "Flight": {
        "gate_id": "Gate",
        "status_id": "FlightStatus",
    },
}

RULE_MANAGED_READONLY_FIELDS = {
    "Gate": {"flight_count", "total_delay_minutes"},
    "Flight": {"status_code", "is_departed"},
}

EXPECTED_RELATIONSHIP_NAMES = {
    "Gate": {"flights"},
    "Flight": {"gate", "status"},
    "FlightStatus": {"flights"},
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
    if session.query(FlightStatus).count():
        return

    scheduled = FlightStatus(code="scheduled", label="Scheduled", is_departed=False)
    delayed = FlightStatus(code="delayed", label="Delayed", is_departed=False)
    departed = FlightStatus(code="departed", label="Departed", is_departed=True)
    session.add_all([scheduled, delayed, departed])
    session.flush()

    gate_a1 = Gate(code="A1", terminal="North")
    gate_b4 = Gate(code="B4", terminal="South")
    session.add_all([gate_a1, gate_b4])
    session.flush()

    session.add_all(
        [
            Flight(
                flight_number="NW102",
                destination="Seattle",
                scheduled_departure=datetime(2026, 3, 13, 9, 15, 0),
                actual_departure=None,
                delay_minutes=0,
                gate_id=gate_a1.id,
                status_id=scheduled.id,
            ),
            Flight(
                flight_number="SA221",
                destination="Denver",
                scheduled_departure=datetime(2026, 3, 13, 9, 40, 0),
                actual_departure=None,
                delay_minutes=25,
                gate_id=gate_a1.id,
                status_id=delayed.id,
            ),
            Flight(
                flight_number="PX404",
                destination="Austin",
                scheduled_departure=datetime(2026, 3, 13, 8, 55, 0),
                actual_departure=datetime(2026, 3, 13, 9, 2, 0),
                delay_minutes=7,
                gate_id=gate_b4.id,
                status_id=departed.id,
            ),
        ]
    )
    session.flush()
