from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
import sys

import yaml


DEFAULT_ABOUT = {
    "recent_changes": "works with modified safrs-react-admin",
    "version": "0.0.0",
}

DEFAULT_API_ROOT = "{http_type}://{swagger_host}:{port}/{api}"
DEFAULT_AUTHENTICATION = "{system-default}"

DEFAULT_SETTINGS: dict[str, Any] = {
    "HomeJS": "/admin-app/home.js",
    "max_list_columns": 8,
    "style_guide": {
        "applicationLocales": ["en", "es"],
        "currency_symbol": "$",
        "currency_symbol_position": "left",
        "date_format": "LL",
        "decimal_max": "1000000000",
        "decimal_min": "2",
        "decimal_separator": ".",
        "detail_mode": "tab",
        "edit_on_mode": "dblclick",
        "exclude_listpicker": False,
        "include_translation": "false",
        "keycloak_client_id": "alsclient",
        "keycloak_realm": "kcals",
        "keycloak_url": "http://localhost:8080",
        "locale": "en",
        "max_decimal_digits": "4",
        "min_decimal_digits": "2",
        "new_mode": "dialog",
        "pick_style": "list",
        "row_height": "small,",
        "serviceType": "JSONAPI",
        "startSessionPath": "/auth/login",
        "style": "light",
        "thousand_separator": ",",
        "use_keycloak": "false",
    },
}


def load_openapi(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"OpenAPI file not found: {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def load_admin_yaml(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return yaml.safe_load(path.read_text()) or {}


def _extract_name_from_ref(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def _resource_from_identifier_ref(ref: str) -> str:
    name = _extract_name_from_ref(ref)
    if name.endswith("ResourceIdentifier"):
        return name[: -len("ResourceIdentifier")]
    if name.endswith("Resource"):
        return name[: -len("Resource")]
    return name


def _resource_from_document_ref(ref: str) -> str | None:
    name = _extract_name_from_ref(ref)
    for suffix in ("DocumentCollection", "DocumentSingle", "DocumentCreate", "DocumentPatch"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return None


def _unwrap_anyof(schema: Mapping[str, Any] | None) -> dict[str, Any]:
    if not schema:
        return {}
    if "$ref" in schema:
        return dict(schema)
    anyof = schema.get("anyOf")
    if isinstance(anyof, list):
        for item in anyof:
            if isinstance(item, Mapping) and "$ref" in item:
                return dict(item)
            if isinstance(item, Mapping) and item.get("type") != "null":
                return dict(item)
    return dict(schema)


def _resolve_schema(openapi: Mapping[str, Any], schema: Mapping[str, Any] | None) -> dict[str, Any]:
    resolved = _unwrap_anyof(schema)
    ref = resolved.get("$ref")
    if isinstance(ref, str):
        return _get_schema(openapi, _extract_name_from_ref(ref))
    return resolved


def _get_schema(openapi: Mapping[str, Any], name: str) -> dict[str, Any]:
    schemas = openapi.get("components", {}).get("schemas", {})
    schema = schemas.get(name)
    if not isinstance(schema, Mapping):
        return {}
    return dict(schema)


def _jsonapi_schema_ref(content: Mapping[str, Any] | None) -> str | None:
    if not isinstance(content, Mapping):
        return None
    preferred = content.get("application/vnd.api+json")
    if isinstance(preferred, Mapping):
        ref = preferred.get("schema", {}).get("$ref")
        if isinstance(ref, str):
            return ref
    for media in content.values():
        if not isinstance(media, Mapping):
            continue
        ref = media.get("schema", {}).get("$ref")
        if isinstance(ref, str):
            return ref
    return None


def _resource_name_from_collection_operation(operation: Mapping[str, Any]) -> str | None:
    responses = operation.get("responses", {})
    if isinstance(responses, Mapping):
        for status_code in ("200", "201", "202"):
            response = responses.get(status_code)
            if not isinstance(response, Mapping):
                continue
            ref = _jsonapi_schema_ref(response.get("content"))
            if isinstance(ref, str):
                resource = _resource_from_document_ref(ref)
                if resource:
                    return resource
    request_body = operation.get("requestBody")
    if isinstance(request_body, Mapping):
        ref = _jsonapi_schema_ref(request_body.get("content"))
        if isinstance(ref, str):
            resource = _resource_from_document_ref(ref)
            if resource:
                return resource
    return None


def _collection_resource_names(openapi: Mapping[str, Any]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for path, path_item in openapi.get("paths", {}).items():
        parts = [part for part in path.split("/") if part]
        if len(parts) == 2 and parts[0] == "api":
            name = None
            if isinstance(path_item, Mapping):
                for method in ("get", "post"):
                    operation = path_item.get(method)
                    if not isinstance(operation, Mapping):
                        continue
                    name = _resource_name_from_collection_operation(operation)
                    if name:
                        break
            if not name:
                continue
            if name not in seen:
                names.append(name)
                seen.add(name)
    return names


def _humanize_name(name: str) -> str:
    if name.endswith("_ColumnName"):
        name = name[: -len("_ColumnName")]
    if name.islower():
        return name
    name = name.replace("_", " ")
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def _is_string_attr(schema: Mapping[str, Any]) -> bool:
    schema = _unwrap_anyof(schema)
    if schema.get("type") == "string":
        return True
    anyof = schema.get("anyOf")
    if isinstance(anyof, list):
        return any(
            isinstance(item, Mapping) and item.get("type") == "string"
            for item in anyof
        )
    return False


def _is_number_attr(schema: Mapping[str, Any]) -> bool:
    schema = _unwrap_anyof(schema)
    if schema.get("type") == "number":
        return True
    anyof = schema.get("anyOf")
    if isinstance(anyof, list):
        return any(
            isinstance(item, Mapping) and item.get("type") == "number"
            for item in anyof
        )
    return False


def _attr_type(schema: Mapping[str, Any]) -> str | None:
    if _is_number_attr(schema):
        return "DECIMAL"
    return None


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _choose_user_key(
    attr_names: Iterable[str],
    attr_map: Mapping[str, Mapping[str, Any]],
) -> str | None:
    attrs = list(attr_names)
    if not attrs:
        return None

    def score(name: str) -> tuple[int, int]:
        normalized = _normalize_name(name)
        rank = 0
        schema = _unwrap_anyof(attr_map.get(name))
        is_string = _is_string_attr(schema)

        if is_string:
            rank += 20
        if name == "Id":
            rank += 30
        if normalized == "id":
            rank += 30
        if "columnname" in normalized:
            rank += 80
        if normalized.endswith("name"):
            rank += 70
        if normalized == "name":
            rank += 10
        if normalized.endswith("label"):
            rank += 68
        if normalized.endswith("description"):
            rank += 65
        if normalized.endswith("title"):
            rank += 60
        if normalized.endswith("displayname"):
            rank += 60
        if normalized.endswith("code"):
            rank += 50
        if normalized.endswith("email"):
            rank += 45
        if normalized.endswith("slug"):
            rank += 40
        if normalized.endswith("id") and normalized != "id":
            rank -= 40
        if normalized == "notes":
            rank -= 20
        if normalized.endswith("notes"):
            rank -= 10
        if normalized.endswith("count") or normalized.startswith("count"):
            rank -= 15
        if normalized.startswith("is") or normalized.startswith("has"):
            rank -= 10
        if not is_string:
            rank -= 5
        return (rank, -attrs.index(name))

    return max(attrs, key=score)


def _required_attribute_names(openapi: Mapping[str, Any], resource: str) -> set[str]:
    create_schema = _get_schema(openapi, f"{resource}CreateResource")
    required = set()

    if "id" in create_schema.get("required", []):
        attr_names = {name for name, _ in _resource_attributes(openapi, resource)}
        if "Id" in attr_names:
            required.add("Id")
        elif "id" in attr_names:
            required.add("id")

    attributes_schema = _resolve_schema(
        openapi,
        create_schema.get("properties", {}).get("attributes"),
    )
    for name in attributes_schema.get("required", []):
        if isinstance(name, str):
            required.add(name)

    return required


def _relationship_target_resource(schema: Mapping[str, Any]) -> str | None:
    data_schema = schema.get("properties", {}).get("data")
    if not isinstance(data_schema, Mapping):
        return None
    if "items" in data_schema:
        items = data_schema.get("items")
        if isinstance(items, Mapping) and "$ref" in items:
            return _resource_from_identifier_ref(str(items["$ref"]))
        return None
    if "$ref" in data_schema:
        return _resource_from_identifier_ref(str(data_schema["$ref"]))
    if "anyOf" in data_schema:
        for item in data_schema.get("anyOf", []):
            if isinstance(item, Mapping) and "$ref" in item:
                return _resource_from_identifier_ref(str(item["$ref"]))
    return None


def _relationship_direction(schema: Mapping[str, Any]) -> str | None:
    data_schema = schema.get("properties", {}).get("data")
    if not isinstance(data_schema, Mapping):
        return None
    if "items" in data_schema:
        return "tomany"
    if "$ref" in data_schema:
        return "toone"
    if "anyOf" in data_schema:
        for item in data_schema.get("anyOf", []):
            if isinstance(item, Mapping) and "$ref" in item:
                return "toone"
            if isinstance(item, Mapping) and "items" in item:
                return "tomany"
    return None


def _resource_attributes(openapi: Mapping[str, Any], resource: str) -> list[tuple[str, dict[str, Any]]]:
    schema = _get_schema(openapi, f"{resource}Attributes")
    props = schema.get("properties", {})
    if not isinstance(props, Mapping):
        return []
    attrs: list[tuple[str, dict[str, Any]]] = []
    for name, raw_schema in props.items():
        if isinstance(raw_schema, Mapping):
            attrs.append((name, dict(raw_schema)))
    return attrs


def _source_relationship_fks(
    openapi: Mapping[str, Any],
    resource: str,
    relationship_name: str,
    target_resource: str,
) -> list[str]:
    attrs = _resource_attributes(openapi, resource)
    attr_names = [name for name, _ in attrs]
    target_attr_names = {
        _normalize_name(name)
        for name, _ in _resource_attributes(openapi, target_resource)
    }
    target_norm = _normalize_name(target_resource)
    rel_norm = _normalize_name(relationship_name)

    direct_candidates: list[str] = []
    shared_candidates: list[str] = []

    for name in attr_names:
        normalized = _normalize_name(name)
        if normalized == f"{rel_norm}id" or normalized == f"{target_norm}id":
            direct_candidates.append(name)
            continue
        if normalized == rel_norm or normalized == target_norm:
            direct_candidates.append(name)
            continue
        if normalized.endswith(rel_norm) or normalized.endswith(target_norm):
            direct_candidates.append(name)
            continue
        if (normalized.startswith(rel_norm) or normalized.startswith(target_norm)) and normalized.endswith("id"):
            direct_candidates.append(name)
            continue
        if resource != target_resource and target_attr_names and normalized in target_attr_names:
            shared_candidates.append(name)

    if direct_candidates:
        return direct_candidates
    return sorted(shared_candidates, key=lambda item: item.lower())


def _promoted_relationship_fks(
    openapi: Mapping[str, Any],
    resource: str,
    relationship_name: str,
    target_resource: str,
) -> list[str]:
    attrs = _source_relationship_fks(openapi, resource, relationship_name, target_resource)
    source_attrs = [name for name, _ in _resource_attributes(openapi, resource)]
    source_positions = {name: idx for idx, name in enumerate(source_attrs)}
    promoted: list[str] = []
    for name in attrs:
        normalized = _normalize_name(name)
        if normalized.endswith("id") or normalized == "id" or normalized in {_normalize_name(resource), _normalize_name(target_resource), _normalize_name(relationship_name)}:
            promoted.append(name)
            continue
        if normalized in {_normalize_name(resource), _normalize_name(target_resource), _normalize_name(relationship_name)}:
            promoted.append(name)
            continue
        if normalized.endswith("order") or normalized.endswith("name"):
            promoted.append(name)
            continue
    promoted.sort(key=lambda item: source_positions.get(item, 0))
    return promoted


def _tab_groups_for_resource(openapi: Mapping[str, Any], resource: str) -> list[dict[str, Any]]:
    relationships = _get_schema(openapi, f"{resource}Relationships")
    props = relationships.get("properties", {})
    if not isinstance(props, Mapping):
        return []

    tomany_groups: list[dict[str, Any]] = []
    toone_groups: list[dict[str, Any]] = []
    for rel_name, raw_schema in props.items():
        if not isinstance(raw_schema, Mapping):
            continue
        schema = _resolve_schema(openapi, raw_schema)
        if not schema:
            continue
        direction = _relationship_direction(schema)
        target = _relationship_target_resource(schema)
        if direction not in {"toone", "tomany"} or not target:
            continue
        if direction == "toone":
            fks = _source_relationship_fks(openapi, resource, rel_name, target)
        else:
            fks = []
            child_relationships = _get_schema(openapi, f"{target}Relationships")
            child_props = child_relationships.get("properties", {})
            if isinstance(child_props, Mapping):
                for child_rel_name, child_raw_schema in child_props.items():
                    if not isinstance(child_raw_schema, Mapping):
                        continue
                    child_schema = _resolve_schema(openapi, child_raw_schema)
                    child_direction = _relationship_direction(child_schema)
                    child_target = _relationship_target_resource(child_schema)
                    if child_direction != "toone" or child_target != resource:
                        continue
                    child_fks = _source_relationship_fks(openapi, target, child_rel_name, resource)
                    for fk in child_fks:
                        if fk not in fks:
                            fks.append(fk)
        group = (
            {
                "direction": direction,
                "fks": fks,
                "name": rel_name,
                "resource": target,
            }
        )
        if direction == "tomany":
            tomany_groups.append(group)
        else:
            toone_groups.append(group)
    return tomany_groups + toone_groups


def _ordered_attributes(
    openapi: Mapping[str, Any],
    resource: str,
) -> list[dict[str, Any]]:
    attrs = _resource_attributes(openapi, resource)
    attr_order = [name for name, _ in attrs]
    attr_map = {name: schema for name, schema in attrs}
    user_key = _choose_user_key(attr_order, attr_map)
    required_attrs = _required_attribute_names(openapi, resource)
    promoted_fks: list[str] = []

    relationships = _get_schema(openapi, f"{resource}Relationships")
    props = relationships.get("properties", {})
    if isinstance(props, Mapping):
        for rel_name, raw_schema in props.items():
            if not isinstance(raw_schema, Mapping):
                continue
            schema = _resolve_schema(openapi, raw_schema)
            direction = _relationship_direction(schema)
            target = _relationship_target_resource(schema)
            if direction != "toone" or not target:
                continue
            for fk in _promoted_relationship_fks(openapi, resource, rel_name, target):
                if fk not in promoted_fks:
                    promoted_fks.append(fk)

    ordered_names: list[str] = []
    if user_key and user_key in attr_map:
        ordered_names.append(user_key)
    for fk in promoted_fks:
        if fk in attr_map and fk not in ordered_names:
            ordered_names.append(fk)

    remaining = [name for name in attr_order if name not in ordered_names]
    id_attrs = [name for name in remaining if _normalize_name(name) == "id"]
    remaining = [name for name in remaining if name not in id_attrs]

    ordered_names.extend(remaining)
    ordered_names.extend(id_attrs)

    attributes: list[dict[str, Any]] = []
    for name in ordered_names:
        schema = attr_map[name]
        item: dict[str, Any] = {"name": name}
        if user_key and name == user_key:
            item["label"] = f" {_humanize_name(name)}*"
            item["search"] = True
            item["sort"] = True
        if name in required_attrs:
            item["required"] = True
        attr_type = _attr_type(schema)
        if attr_type:
            item["type"] = attr_type
        attributes.append(item)
    return attributes


def _resource_block(openapi: Mapping[str, Any], resource: str) -> dict[str, Any]:
    attrs = _resource_attributes(openapi, resource)
    attr_map = {name: schema for name, schema in attrs}
    user_key = _choose_user_key([name for name, _ in attrs], attr_map)
    block: dict[str, Any] = {
        "attributes": _ordered_attributes(openapi, resource),
        "type": resource,
    }
    if user_key:
        block["user_key"] = user_key
    tab_groups = _tab_groups_for_resource(openapi, resource)
    if tab_groups:
        block["tab_groups"] = tab_groups
    return block


def build_admin_yaml(
    openapi: Mapping[str, Any],
    *,
    about_date: str | None = None,
    template_admin: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    template = dict(template_admin or {})
    resource_names = _collection_resource_names(openapi)
    if not resource_names:
        raise ValueError("No SAFRS JSON:API collection routes found in the OpenAPI schema")
    resources = {name: _resource_block(openapi, name) for name in resource_names}
    tab_group_count = sum(len(resource.get("tab_groups", [])) for resource in resources.values())

    about = dict(DEFAULT_ABOUT)
    about.update(template.get("about", {}))
    about["date"] = about_date or about.get("date") or _format_now()

    info = {
        "number_relationships": tab_group_count,
        "number_tables": len(resources),
    }

    result: dict[str, Any] = {
        "about": about,
        "api_root": template.get("api_root", DEFAULT_API_ROOT),
        "_authentication": template.get("_authentication", DEFAULT_AUTHENTICATION),
        "info": info,
        "info_toggle_checked": template.get("info_toggle_checked", True),
        "resources": resources,
        "settings": template.get("settings", DEFAULT_SETTINGS),
    }
    return result


def _format_now() -> str:
    formatted = datetime.now().strftime("%B %d, %Y %H:%M:%S")
    return formatted.replace(" 0", " ")


def write_admin_yaml(admin_yaml: Mapping[str, Any], output_path: Path) -> None:
    output_path.write_text(
        yaml.safe_dump(admin_yaml, sort_keys=False, allow_unicode=True),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a raw playbook admin.yaml file from SAFRS OpenAPI.",
    )
    parser.add_argument("openapi_json", type=Path, help="Input jsonapi.json/OpenAPI file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output admin.yaml path. If omitted, writes to stdout.",
    )
    parser.add_argument(
        "--template-admin",
        type=Path,
        help="Optional existing admin.yaml whose static top-level keys are reused.",
    )
    parser.add_argument(
        "--about-date",
        help="Override the generated about.date field.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    openapi = load_openapi(args.openapi_json)
    template = load_admin_yaml(args.template_admin)
    admin_yaml = build_admin_yaml(openapi, about_date=args.about_date, template_admin=template)
    rendered = yaml.safe_dump(admin_yaml, sort_keys=False, allow_unicode=True)
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0
    return 0


def main_entry(argv: list[str] | None = None) -> int:
    try:
        return main(argv)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main_entry())
