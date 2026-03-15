from __future__ import annotations

from datetime import datetime

import yaml

from .config import Settings
from .models import ConfigurationItem, OperationalStatus, Service

REQUIRED_RESOURCES = {
    "Service": "/api/services",
    "ConfigurationItem": "/api/configuration_items",
    "OperationalStatus": "/api/operational_statuses",
}

REQUIRED_USER_KEYS = {
    "Service": "code",
    "ConfigurationItem": "hostname",
    "OperationalStatus": "label",
}

REQUIRED_LABELS = {
    "Service": "Services",
    "ConfigurationItem": "Configuration Items",
    "OperationalStatus": "Operational Statuses",
}

REQUIRED_FIELDS = {
    "Service": {
        "id",
        "code",
        "name",
        "owner_name",
        "ci_count",
        "operational_ci_count",
        "total_risk_score",
    },
    "ConfigurationItem": {
        "id",
        "name",
        "ci_class",
        "environment",
        "hostname",
        "ip_address",
        "last_verified_at",
        "risk_score",
        "service_id",
        "status_id",
        "status_code",
        "is_operational",
        "operational_value",
    },
    "OperationalStatus": {
        "id",
        "code",
        "label",
        "is_operational",
        "operational_value",
    },
}

REQUIRED_TRUE_FIELDS = {
    "Service": {"code", "name", "owner_name"},
    "ConfigurationItem": {
        "name",
        "ci_class",
        "environment",
        "hostname",
        "ip_address",
        "risk_score",
        "service_id",
        "status_id",
    },
    "OperationalStatus": {"code", "label", "is_operational", "operational_value"},
}

REQUIRED_REFERENCE_TARGETS = {
    "ConfigurationItem": {
        "service_id": "Service",
        "status_id": "OperationalStatus",
    },
}

RULE_MANAGED_READONLY_FIELDS = {
    "Service": {"ci_count", "operational_ci_count", "total_risk_score"},
    "ConfigurationItem": {"status_code", "is_operational", "operational_value"},
}

EXPECTED_RELATIONSHIP_NAMES = {
    "Service": {"items"},
    "ConfigurationItem": {"service", "status"},
    "OperationalStatus": {"items"},
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
    if session.query(OperationalStatus).count():
        return

    healthy = OperationalStatus(
        code="healthy",
        label="Healthy",
        is_operational=True,
        operational_value=1,
    )
    maintenance = OperationalStatus(
        code="maintenance",
        label="Maintenance",
        is_operational=False,
        operational_value=0,
    )
    retired = OperationalStatus(
        code="retired",
        label="Retired",
        is_operational=False,
        operational_value=0,
    )
    session.add_all([healthy, maintenance, retired])
    session.flush()

    commerce = Service(
        code="COMMERCE",
        name="Commerce Platform",
        owner_name="Ava Patel",
    )
    workplace = Service(
        code="WORKPLACE",
        name="Workplace Systems",
        owner_name="Nico Flores",
    )
    session.add_all([commerce, workplace])
    session.flush()

    session.add_all(
        [
            ConfigurationItem(
                name="API Gateway",
                ci_class="Application",
                environment="production",
                hostname="api-gw-prod-01",
                ip_address="10.10.20.15",
                last_verified_at=datetime(2026, 3, 14, 8, 30, 0),
                risk_score=4.5,
                service_id=commerce.id,
                status_id=healthy.id,
            ),
            ConfigurationItem(
                name="Payments Primary DB",
                ci_class="Database",
                environment="production",
                hostname="payments-db-prod-01",
                ip_address="10.10.30.12",
                last_verified_at=datetime(2026, 3, 14, 7, 55, 0),
                risk_score=8.0,
                service_id=commerce.id,
                status_id=maintenance.id,
            ),
            ConfigurationItem(
                name="HR Portal",
                ci_class="Application",
                environment="staging",
                hostname="hr-portal-stg-01",
                ip_address="10.20.10.21",
                last_verified_at=None,
                risk_score=2.5,
                service_id=workplace.id,
                status_id=healthy.id,
            ),
            ConfigurationItem(
                name="People Batch Runner",
                ci_class="Job Runner",
                environment="development",
                hostname="people-batch-dev-01",
                ip_address="10.20.40.8",
                last_verified_at=None,
                risk_score=6.0,
                service_id=workplace.id,
                status_id=retired.id,
            ),
        ]
    )
    session.flush()
