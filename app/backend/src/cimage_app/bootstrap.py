from __future__ import annotations

from datetime import datetime

import yaml

from .config import Settings
from .models import Gallery, ImageAsset, ShareStatus

REQUIRED_RESOURCES = {
    "Gallery": "/api/galleries",
    "ImageAsset": "/api/image_assets",
    "ShareStatus": "/api/share_statuses",
}

REQUIRED_USER_KEYS = {
    "Gallery": "code",
    "ImageAsset": "title",
    "ShareStatus": "label",
}

REQUIRED_LABELS = {
    "Gallery": "Galleries",
    "ImageAsset": "Images",
    "ShareStatus": "Share Statuses",
}

REQUIRED_FIELDS = {
    "Gallery": {
        "id",
        "code",
        "name",
        "owner_name",
        "image_count",
        "public_image_count",
        "total_size_mb",
    },
    "ImageAsset": {
        "id",
        "title",
        "filename",
        "preview_url",
        "uploaded_at",
        "published_at",
        "file_size_mb",
        "gallery_id",
        "status_id",
        "share_status_code",
        "is_public",
        "public_value",
    },
    "ShareStatus": {"id", "code", "label", "is_public", "public_value"},
}

REQUIRED_TRUE_FIELDS = {
    "Gallery": {"code", "name", "owner_name"},
    "ImageAsset": {
        "title",
        "filename",
        "preview_url",
        "uploaded_at",
        "file_size_mb",
        "gallery_id",
        "status_id",
    },
    "ShareStatus": {"code", "label", "is_public", "public_value"},
}

REQUIRED_REFERENCE_TARGETS = {
    "ImageAsset": {
        "gallery_id": "Gallery",
        "status_id": "ShareStatus",
    },
}

RULE_MANAGED_READONLY_FIELDS = {
    "Gallery": {"image_count", "public_image_count", "total_size_mb"},
    "ImageAsset": {"share_status_code", "is_public", "public_value"},
}

EXPECTED_RELATIONSHIP_NAMES = {
    "Gallery": {"images"},
    "ImageAsset": {"gallery", "status"},
    "ShareStatus": {"images"},
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
    if session.query(ShareStatus).count():
        return

    draft = ShareStatus(code="draft", label="Draft", is_public=False, public_value=0)
    team = ShareStatus(code="team", label="Team Only", is_public=False, public_value=0)
    public = ShareStatus(code="public", label="Public", is_public=True, public_value=1)
    session.add_all([draft, team, public])
    session.flush()

    seattle = Gallery(code="SEA-SET", name="Seattle Set", owner_name="Mina Cole")
    studio = Gallery(code="STUDIO", name="Studio Archive", owner_name="Ravi Hale")
    session.add_all([seattle, studio])
    session.flush()

    session.add_all(
        [
            ImageAsset(
                title="Harbor Dawn",
                filename="harbor-dawn.jpg",
                preview_url="https://cdn.cimage.test/previews/harbor-dawn.jpg",
                uploaded_at=datetime(2026, 3, 13, 9, 15, 0),
                published_at=datetime(2026, 3, 13, 9, 30, 0),
                file_size_mb=6.5,
                gallery_id=seattle.id,
                status_id=public.id,
            ),
            ImageAsset(
                title="Pier Notes",
                filename="pier-notes.png",
                preview_url="https://cdn.cimage.test/previews/pier-notes.png",
                uploaded_at=datetime(2026, 3, 13, 9, 45, 0),
                published_at=None,
                file_size_mb=4.2,
                gallery_id=seattle.id,
                status_id=draft.id,
            ),
            ImageAsset(
                title="Backdrop Study",
                filename="backdrop-study.jpg",
                preview_url="https://cdn.cimage.test/previews/backdrop-study.jpg",
                uploaded_at=datetime(2026, 3, 13, 10, 5, 0),
                published_at=None,
                file_size_mb=8.0,
                gallery_id=studio.id,
                status_id=team.id,
            ),
            ImageAsset(
                title="Launch Poster",
                filename="launch-poster.jpg",
                preview_url="https://cdn.cimage.test/previews/launch-poster.jpg",
                uploaded_at=datetime(2026, 3, 13, 10, 20, 0),
                published_at=datetime(2026, 3, 13, 11, 0, 0),
                file_size_mb=12.3,
                gallery_id=studio.id,
                status_id=public.id,
            ),
        ]
    )
    session.flush()
