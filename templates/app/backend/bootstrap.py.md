# `backend/src/my_app/bootstrap.py`

See also:

- [../../../specs/contracts/backend/bootstrap-and-db-lifecycle.md](../../../specs/contracts/backend/bootstrap-and-db-lifecycle.md)
- [../../../specs/contracts/backend/models-and-naming.md](../../../specs/contracts/backend/models-and-naming.md)

```python
from __future__ import annotations

from datetime import datetime

import yaml

from .config import Settings
from .models import Collection, Item, Status

REQUIRED_RESOURCE_KEYS = {
    "Collection",
    "Item",
    "Status",
}

REQUIRED_USER_KEYS = {
    "Collection": "name",
    "Item": "title",
    "Status": "label",
}

REQUIRED_LABELS = {
    "Collection": "Collections",
    "Item": "Items",
    "Status": "Statuses",
}

REQUIRED_FIELDS = {
    "Collection": {"id", "name", "item_count", "total_estimate_hours"},
    "Item": {
        "id",
        "title",
        "estimate_hours",
        "completed_at",
        "collection_id",
        "status_id",
        "status_code",
        "is_completed",
    },
    "Status": {"id", "code", "label", "is_closed"},
}

REQUIRED_TRUE_FIELDS = {
    "Collection": {"name"},
    "Item": {"title", "estimate_hours", "collection_id", "status_id"},
    "Status": {"code", "label"},
}

REQUIRED_REFERENCE_TARGETS = {
    "Item": {
        "collection_id": "Collection",
        "status_id": "Status",
    }
}

RULE_MANAGED_READONLY_FIELDS = {
    "Collection": {"item_count", "total_estimate_hours"},
    "Item": {"status_code", "is_completed"},
}

EXPECTED_RELATIONSHIP_NAMES = {
    "Collection": {"items"},
    "Item": {"collection", "status"},
    "Status": {"items"},
}

SEARCHABLE_TYPES = {"text"}


def validate_admin_schema(settings: Settings) -> dict:
    content = yaml.safe_load(settings.admin_yaml_path.read_text())
    resources = (content or {}).get("resources", {})
    for resource_name in REQUIRED_RESOURCE_KEYS:
        resource = resources.get(resource_name)
        if resource is None:
            raise ValueError(f"admin.yaml is missing resource {resource_name}")
        endpoint = resource.get("endpoint")
        if not isinstance(endpoint, str) or not endpoint.startswith("/api/"):
            raise ValueError(
                f"admin.yaml resource {resource_name} must declare a provisional /api/... endpoint string"
            )
        if resource.get("label") != REQUIRED_LABELS[resource_name]:
            raise ValueError(
                f"admin.yaml resource {resource_name} has label {resource.get('label')!r}, expected {REQUIRED_LABELS[resource_name]!r}"
            )
        if resource.get("user_key") != REQUIRED_USER_KEYS[resource_name]:
            raise ValueError(
                f"admin.yaml resource {resource_name} has user_key {resource.get('user_key')!r}, expected {REQUIRED_USER_KEYS[resource_name]!r}"
            )

        attributes = resource.get("attributes") or {}
        missing = sorted(REQUIRED_FIELDS[resource_name] - set(attributes))
        if missing:
            raise ValueError(
                f"admin.yaml resource {resource_name} is missing required attributes {missing!r}"
            )

        if resource.get("user_key") not in attributes:
            raise ValueError(
                f"admin.yaml resource {resource_name} user_key {resource.get('user_key')!r} is not declared in attributes"
            )

        for field_name in REQUIRED_TRUE_FIELDS.get(resource_name, set()):
            if attributes[field_name].get("required") is not True:
                raise ValueError(
                    f"admin.yaml attribute {resource_name}.{field_name} must declare required: true"
                )

        for field_name, reference_target in REQUIRED_REFERENCE_TARGETS.get(resource_name, {}).items():
            config = attributes[field_name]
            if config.get("type") != "reference":
                raise ValueError(
                    f"admin.yaml attribute {resource_name}.{field_name} must use type: reference"
                )
            if config.get("reference") != reference_target:
                raise ValueError(
                    f"admin.yaml attribute {resource_name}.{field_name} has reference {config.get('reference')!r}, expected {reference_target!r}"
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
                    f"admin.yaml attribute {resource_name}.{attribute_name} uses search=true with unsupported type {config.get('type')!r}"
                )

        for group_name, group in (resource.get("tab_groups") or {}).items():
            relationships = group.get("relationships") or []
            for relationship_name in relationships:
                if relationship_name not in EXPECTED_RELATIONSHIP_NAMES.get(resource_name, set()):
                    raise ValueError(
                        f"admin.yaml tab_groups entry {resource_name}.{group_name} references unknown relationship {relationship_name!r}"
                    )

    return content


def seed_reference_data(session) -> None:
    if session.query(Status).count():
        return

    scheduled = Status(code="scheduled", label="Scheduled", is_closed=False)
    done = Status(code="done", label="Done", is_closed=True)
    blocked = Status(code="blocked", label="Blocked", is_closed=False)
    session.add_all([scheduled, done, blocked])
    session.flush()

    collection = Collection(name="Spring Planning")
    session.add(collection)
    session.flush()

    session.add_all(
        [
            Item(
                title="Board passengers",
                estimate_hours=2.5,
                completed_at=None,
                collection_id=collection.id,
                status_id=scheduled.id,
            ),
            Item(
                title="Close manifest",
                estimate_hours=3.0,
                completed_at=datetime.utcnow(),
                collection_id=collection.id,
                status_id=done.id,
            ),
        ]
    )
    session.flush()
```

Notes:

- This is a starter-lane implementation template. For a `rename-only` or
  `non-starter` run, the Backend role MUST rewrite the starter-specific
  constant blocks before treating this file as implementation-ready.
- Validate `admin.yaml` static contract shape before exposing routes.
- Seed only on an empty DB.
- The seed must be idempotent.
- Let activated LogicBank rules populate derived columns through normal ORM
  writes and commit, rather than using a manual refresh helper.
- Exact collection-path validation belongs in post-startup integration tests,
  not in this pre-route bootstrap validator.
- For a non-starter domain, the implementation MUST rewrite these constant
  blocks together:
  - `REQUIRED_RESOURCE_KEYS`
  - `REQUIRED_USER_KEYS`
  - `REQUIRED_LABELS`
  - `REQUIRED_FIELDS`
  - `REQUIRED_TRUE_FIELDS`
  - `REQUIRED_REFERENCE_TARGETS`
  - `RULE_MANAGED_READONLY_FIELDS`
  - `EXPECTED_RELATIONSHIP_NAMES`
