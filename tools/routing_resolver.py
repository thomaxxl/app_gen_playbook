from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from execution_scope import active_scope_context
from orchestrator_common import path_matches_rule, relpath, role_state_dir_names


CHANGE_RUN_MODES = {"iterative-change-run", "app-only-hotfix"}
CHANGE_PHASE_PREFIX = "phase-I"
STRICT_ROLE_LOAD_PHASE_PREFIXES = (
    "phase-I4",
    "phase-I5",
    "phase-I6",
    "phase-I7",
)
PLACEHOLDER_PREFIXES = (
    "fill with ",
    "fill only ",
    "fill ",
    "(none)",
)
MESSAGE_SCOPED_WRITE_PREFIXES = (
    "runs/current/",
    "app/",
    "playbook/",
    "scripts/",
    "tools/",
)
DEFAULT_CHANGE_ARTIFACT_RULES = {
    "product_manager": (
        "runs/current/artifacts/product/**",
        "runs/current/artifacts/architecture/**",
        "runs/current/evidence/**",
        "runs/current/changes/*/candidate/artifacts/product/**",
    ),
    "architect": (
        "runs/current/artifacts/product/**",
        "runs/current/artifacts/architecture/**",
        "runs/current/artifacts/ux/**",
        "runs/current/artifacts/backend-design/**",
        "runs/current/evidence/**",
        "runs/current/changes/*/candidate/artifacts/architecture/**",
    ),
    "frontend": (
        "runs/current/artifacts/ux/**",
        "runs/current/artifacts/architecture/**",
        "runs/current/evidence/**",
        "runs/current/changes/*/candidate/artifacts/ux/**",
    ),
    "backend": (
        "runs/current/artifacts/backend-design/**",
        "runs/current/artifacts/architecture/**",
        "runs/current/artifacts/product/business-rules.md",
        "runs/current/artifacts/product/conceptual-domain-model.md",
        "runs/current/artifacts/product/resource-behavior-matrix.md",
        "runs/current/artifacts/product/traceability-matrix.md",
        "runs/current/evidence/**",
        "runs/current/changes/*/candidate/artifacts/backend-design/**",
    ),
    "qa": (
        "runs/current/artifacts/product/**",
        "runs/current/artifacts/architecture/**",
        "runs/current/artifacts/ux/**",
        "runs/current/evidence/**",
    ),
    "deployment": (
        "runs/current/artifacts/devops/**",
        "runs/current/artifacts/architecture/runtime-bom.md",
        "runs/current/artifacts/architecture/dependency-provisioning.md",
        "runs/current/evidence/**",
        "runs/current/changes/*/candidate/artifacts/devops/**",
    ),
    "ceo": (
        "runs/current/**",
        "app/**",
        "playbook/**",
        "scripts/**",
        "tools/**",
    ),
}


def parse_yaml_subset(path: Path) -> Any:
    lines = path.read_text(encoding="utf-8").splitlines()
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    consumed_indexes: set[int] = set()

    for index, raw_line in enumerate(lines):
        if index in consumed_indexes:
            continue
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        text = raw_line.strip()
        line_is_list_item = text.startswith("- ")

        while len(stack) > 1:
            top_indent, top_container = stack[-1]
            if indent > top_indent:
                break
            if indent == top_indent and line_is_list_item and isinstance(top_container, list):
                break
            stack.pop()

        parent = stack[-1][1]

        if line_is_list_item:
            if not isinstance(parent, list):
                raise ValueError(f"Invalid list item in {path}: {raw_line}")
            item_text = text[2:].strip()
            quote_char = item_text[:1] if item_text[:1] in {"'", '"'} else ""
            if quote_char and not item_text.endswith(quote_char):
                scalar_parts = [item_text]
                for candidate_index, candidate in enumerate(lines[index + 1 :], start=index + 1):
                    if not candidate.strip():
                        scalar_parts.append("")
                        consumed_indexes.add(candidate_index)
                        continue
                    candidate_indent = len(candidate) - len(candidate.lstrip(" "))
                    if candidate_indent <= indent:
                        break
                    consumed_indexes.add(candidate_index)
                    scalar_parts.append(candidate.strip())
                    if candidate.strip().endswith(quote_char):
                        break
                parent.append(" ".join(part.strip() for part in scalar_parts if part.strip()).strip(quote_char))
                continue

            continuation_parts: list[str] = []
            for candidate_index, candidate in enumerate(lines[index + 1 :], start=index + 1):
                if not candidate.strip():
                    if continuation_parts:
                        continuation_parts.append("")
                        consumed_indexes.add(candidate_index)
                    continue
                candidate_indent = len(candidate) - len(candidate.lstrip(" "))
                candidate_text = candidate.strip()
                if candidate_indent <= indent or candidate_text.startswith("- "):
                    break
                consumed_indexes.add(candidate_index)
                continuation_parts.append(candidate_text)
            if continuation_parts:
                item_text = " ".join([item_text, *[part for part in continuation_parts if part]])
            parent.append(item_text)
            continue

        if text == "[]":
            if isinstance(parent, list):
                continue
            raise ValueError(f"Invalid empty-list entry in {path}: {raw_line}")

        if text == "{}":
            if isinstance(parent, dict):
                continue
            raise ValueError(f"Invalid empty-mapping entry in {path}: {raw_line}")

        if ":" not in text:
            raise ValueError(f"Invalid mapping entry in {path}: {raw_line}")

        key, remainder = text.split(":", 1)
        key = key.strip()
        remainder = remainder.strip()

        if remainder:
            if not isinstance(parent, dict):
                raise ValueError(f"Invalid scalar parent in {path}: {raw_line}")
            if remainder == "[]":
                parent[key] = []
                continue
            if remainder == "{}":
                parent[key] = {}
                continue
            if remainder in {">", "|"}:
                block_lines: list[str] = []
                for candidate_index, candidate in enumerate(lines[index + 1 :], start=index + 1):
                    if not candidate.strip():
                        if block_lines:
                            block_lines.append("")
                            consumed_indexes.add(candidate_index)
                        continue
                    candidate_indent = len(candidate) - len(candidate.lstrip(" "))
                    if candidate_indent <= indent:
                        break
                    consumed_indexes.add(candidate_index)
                    block_lines.append(candidate[candidate_indent:].rstrip())
                if remainder == ">":
                    folded_parts = [line.strip() for line in block_lines if line.strip()]
                    parent[key] = " ".join(folded_parts)
                else:
                    parent[key] = "\n".join(block_lines)
                continue
            quote_char = remainder[:1] if remainder[:1] in {"'", '"'} else ""
            if quote_char and not remainder.endswith(quote_char):
                scalar_parts = [remainder]
                for candidate_index, candidate in enumerate(lines[index + 1 :], start=index + 1):
                    if not candidate.strip():
                        scalar_parts.append("")
                        consumed_indexes.add(candidate_index)
                        continue
                    candidate_indent = len(candidate) - len(candidate.lstrip(" "))
                    if candidate_indent <= indent:
                        break
                    consumed_indexes.add(candidate_index)
                    scalar_parts.append(candidate.strip())
                    if candidate.strip().endswith(quote_char):
                        break
                parent[key] = " ".join(part.strip() for part in scalar_parts if part.strip()).strip(quote_char)
                continue
            parent[key] = remainder
            continue

        next_container: Any
        next_container = []
        # Look ahead to determine whether this empty key starts a list or dict.
        for candidate in lines[index + 1 :]:
            if not candidate.strip() or candidate.lstrip().startswith("#"):
                continue
            candidate_indent = len(candidate) - len(candidate.lstrip(" "))
            candidate_text = candidate.strip()
            if candidate_indent <= indent:
                break
            if candidate_text == "[]":
                next_container = []
            elif candidate_text == "{}":
                next_container = {}
            else:
                next_container = [] if candidate_text.startswith("- ") else {}
            break

        if not isinstance(parent, dict):
            raise ValueError(f"Invalid nested parent in {path}: {raw_line}")
        parent[key] = next_container
        stack.append((indent, next_container))

    return root


def _repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return relpath(path.resolve(), repo_root)
    except ValueError:
        return str(path.resolve())


def canonical_manifest_role(runtime_role: str) -> str:
    return "devops" if runtime_role == "deployment" else runtime_role


def _load_role_core(repo_root: Path) -> Mapping[str, Any]:
    payload = parse_yaml_subset(repo_root / "playbook" / "routing" / "role-core.yaml")
    if not isinstance(payload, dict):
        raise ValueError("role-core.yaml must decode to a mapping")
    return payload


def _load_phase_bundles(repo_root: Path) -> Mapping[str, Any]:
    payload = parse_yaml_subset(repo_root / "playbook" / "routing" / "phase-bundles.yaml")
    if not isinstance(payload, dict):
        raise ValueError("phase-bundles.yaml must decode to a mapping")
    return payload


def _load_capability_map(repo_root: Path) -> Mapping[str, Any]:
    payload = parse_yaml_subset(repo_root / "playbook" / "routing" / "capability-map.yaml")
    if not isinstance(payload, dict):
        raise ValueError("capability-map.yaml must decode to a mapping")
    return payload


def resolve_role_config(repo_root: Path, runtime_role: str) -> Mapping[str, Any]:
    manifest_role = canonical_manifest_role(runtime_role)
    role_core = _load_role_core(repo_root)
    config = role_core.get(manifest_role)
    if not isinstance(config, dict):
        raise ValueError(f"Unknown role in role-core.yaml: {manifest_role}")
    return config


def enabled_features_for_role(repo_root: Path, runtime_role: str) -> set[str]:
    capability_profile = repo_root / "runs" / "current" / "artifacts" / "architecture" / "capability-profile.md"
    capability_map = _load_capability_map(repo_root)
    manifest_role = canonical_manifest_role(runtime_role)
    enabled: set[str] = set()

    if not capability_profile.exists():
        return enabled

    row_pattern = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*[^|]*\|\s*([^|]+?)\s*\|$")
    for raw_line in capability_profile.read_text(encoding="utf-8").splitlines():
        match = row_pattern.match(raw_line.strip())
        if not match:
            continue
        feature = match.group(1).strip()
        status = match.group(2).strip().lower()
        roles = {part.strip() for part in match.group(3).split(",")}
        if status != "enabled" or manifest_role not in roles:
            continue
        entry = capability_map.get(feature)
        if isinstance(entry, dict):
            enabled.add(feature)

    return enabled


def resolve_phase_bundle(
    repo_root: Path,
    runtime_role: str,
    *,
    explicit_task_bundle: str | None = None,
    explicit_phase: str | None = None,
    message_required_reads: list[str] | None = None,
) -> tuple[str | None, str | None]:
    manifest_role = canonical_manifest_role(runtime_role)
    phase_bundles = _load_phase_bundles(repo_root)
    required_reads = message_required_reads or []

    bundle_candidates: list[str] = []
    if explicit_task_bundle:
        bundle_candidates.append(explicit_task_bundle)
    bundle_candidates.extend(
        path
        for path in required_reads
        if path.startswith("playbook/task-bundles/") and path.endswith(".yaml")
    )

    normalized_phase = (explicit_phase or "").strip().replace("-", "_")
    for phase_name, payload in phase_bundles.items():
        if not isinstance(payload, dict):
            continue

        alias_for = payload.get("alias_for")
        if isinstance(alias_for, str):
            aliased = phase_bundles.get(alias_for)
            if isinstance(aliased, dict):
                payload = aliased

        if normalized_phase and phase_name == normalized_phase:
            bundle = payload.get(manifest_role)
            if isinstance(bundle, str):
                summary = payload.get("summary")
                return summary if isinstance(summary, str) else None, bundle

        for candidate in bundle_candidates:
            if payload.get(manifest_role) == candidate:
                summary = payload.get("summary")
                return summary if isinstance(summary, str) else None, candidate

    # Do not fall back to another role's task bundle just because it appeared
    # in Required Reads. That can silently widen or skew the writable scope for
    # recovery turns that only cite a cross-role review bundle as context.
    if explicit_task_bundle:
        return None, explicit_task_bundle
    return None, None


def _string_list(mapping: Mapping[str, Any], key: str) -> list[str]:
    value = mapping.get(key, [])
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, str):
        return [value]
    return []


def _condition_active(repo_root: Path, condition: str, enabled_features: set[str]) -> bool:
    if condition in enabled_features:
        return True
    if condition == "custom_pages":
        return (repo_root / "runs" / "current" / "artifacts" / "product" / "custom-pages.md").exists()
    return False


def _is_placeholder_value(value: str) -> bool:
    normalized = value.strip().lower()
    return any(normalized.startswith(prefix) for prefix in PLACEHOLDER_PREFIXES)


def _payload_contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return _is_placeholder_value(value) or value.strip() in {"[]", "{}"}
    if isinstance(value, list):
        return any(_payload_contains_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(_payload_contains_placeholder(item) for item in value.values())
    return False


def _clean_declared_paths(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        normalized = value.strip().strip("`")
        if not normalized or normalized in {"[]", "{}"} or _is_placeholder_value(normalized):
            continue
        cleaned.append(normalized)
    return cleaned


def _normalize_message_scoped_path(repo_root: Path, value: str) -> str:
    match = re.search(r"`([^`]+)`", value)
    normalized = match.group(1).strip() if match else value.strip().strip("`")
    if not normalized:
        return ""

    if normalized.startswith(MESSAGE_SCOPED_WRITE_PREFIXES):
        return normalized

    candidate = Path(normalized)
    if candidate.is_absolute():
        try:
            normalized = relpath(candidate, repo_root)
        except ValueError:
            app_root = (repo_root / "app").resolve()
            resolved_candidate = candidate.resolve()
            try:
                normalized = f"app/{resolved_candidate.relative_to(app_root).as_posix()}"
            except ValueError:
                return ""
        return normalized if normalized.startswith(MESSAGE_SCOPED_WRITE_PREFIXES) else ""

    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized if normalized.startswith(MESSAGE_SCOPED_WRITE_PREFIXES) else ""


def resolve_message_scoped_writable_paths(
    repo_root: Path,
    runtime_role: str,
    headers: Mapping[str, Any] | None,
    sections: Mapping[str, Any] | None,
) -> list[str]:
    if not isinstance(headers, Mapping) or not isinstance(sections, Mapping):
        return []

    receiver = str(headers.get("to") or headers.get("receiver") or "").strip().lower()
    if receiver and receiver != runtime_role:
        return []

    sender = str(headers.get("from") or headers.get("sender") or "").strip().lower()
    gate_status = str(sections.get("gate status", "")).strip().lower()
    if gate_status in {"unspecified", ""}:
        gate_status = ""
    if gate_status and gate_status != "blocked":
        return []

    if sender not in {runtime_role, "orchestrator", "ceo"}:
        return []

    required_scope = sections.get("required scope", [])
    if isinstance(required_scope, str):
        scope_values = [required_scope]
    elif isinstance(required_scope, list):
        scope_values = [item for item in required_scope if isinstance(item, str)]
    else:
        return []

    scoped_paths = [
        _normalize_message_scoped_path(repo_root, value)
        for value in scope_values
        if _normalize_message_scoped_path(repo_root, value)
    ]
    return _clean_declared_paths(scoped_paths)


def _parse_markdown_path_list(path: Path) -> list[str]:
    if not path.exists():
        return []

    results: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        code_match = re.match(r"^[-*]\s+`([^`]+)`\s*$", line)
        if code_match:
            results.append(code_match.group(1).strip())
            continue
        text_match = re.match(r"^[-*]\s+(.+?)\s*$", line)
        if text_match:
            value = text_match.group(1).strip()
            if "/" in value or value.endswith((".md", ".yaml", ".json", ".py", ".ts", ".tsx", ".sh")):
                results.append(value.strip("`"))
    return _clean_declared_paths(results)


def _load_run_status(repo_root: Path) -> Mapping[str, Any]:
    path = repo_root / "runs" / "current" / "orchestrator" / "run-status.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _active_change_context(repo_root: Path) -> dict[str, Any] | None:
    status = _load_run_status(repo_root)
    change_id = status.get("change_id")
    if not isinstance(change_id, str) or not change_id.strip():
        return None

    current_phase = str(status.get("current_phase", "")).strip()
    mode = str(status.get("mode", "")).strip()
    if mode not in CHANGE_RUN_MODES and not current_phase.startswith(CHANGE_PHASE_PREFIX):
        return None

    change_root = repo_root / "runs" / "current" / "changes" / change_id
    if not change_root.exists():
        return None

    return {
        "change_id": change_id,
        "change_root": change_root,
        "current_phase": current_phase,
        "classification": active_scope_context(repo_root).get("classification", {}),
        "affected_artifacts": _parse_markdown_path_list(change_root / "affected-artifacts.md"),
        "affected_candidate_artifacts": _parse_markdown_path_list(change_root / "affected-candidate-artifacts.md"),
        "affected_app_paths": _parse_markdown_path_list(change_root / "affected-app-paths.md"),
    }


def _load_external_reference_manifest(change_root: Path) -> tuple[str | None, Mapping[str, Any]]:
    manifest_path = change_root / "external-references" / "manifest.json"
    if not manifest_path.exists():
        return None, {}
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"External reference manifest must decode to a mapping: {manifest_path}")
    return _repo_rel(change_root.parents[3], manifest_path), payload


def _external_reference_read_paths(
    repo_root: Path,
    runtime_role: str,
    change_root: Path,
    payload: Mapping[str, Any],
) -> list[str]:
    read_paths: list[str] = []
    readme_path = change_root / "external-references" / "README.md"
    if readme_path.exists():
        read_paths.append(_repo_rel(repo_root, readme_path))

    requested_skills = payload.get("requested_skill_paths", [])
    if isinstance(requested_skills, list):
        for path_value in requested_skills:
            if isinstance(path_value, str) and path_value.strip():
                read_paths.append(path_value.strip())

    references = payload.get("references", [])
    if not isinstance(references, list):
        return _clean_declared_paths(read_paths)

    for entry in references:
        if not isinstance(entry, dict):
            continue
        roles = entry.get("roles", [])
        if isinstance(roles, list) and roles and runtime_role not in {str(item).strip() for item in roles}:
            continue
        materialized = entry.get("materialized_path")
        if isinstance(materialized, str) and materialized.strip():
            read_paths.append(f"runs/current/changes/{change_root.name}/{materialized.strip()}")
        key_files = entry.get("key_files", [])
        if isinstance(key_files, list):
            for key_file in key_files:
                if isinstance(key_file, str) and key_file.strip():
                    if key_file.startswith("runs/current/changes/") or key_file.startswith("app/") or key_file.startswith("skills/") or key_file.startswith(".codex/skills/"):
                        read_paths.append(key_file.strip())
                    elif key_file.startswith("/"):
                        read_paths.append(key_file.strip())
                    else:
                        read_paths.append(f"runs/current/changes/{change_root.name}/{key_file.strip()}")
    return _clean_declared_paths(read_paths)


def _load_role_load_manifest(change_root: Path, runtime_role: str) -> tuple[str | None, Mapping[str, Any]]:
    manifest_role = canonical_manifest_role(runtime_role)
    manifest_path = change_root / "role-loads" / f"{manifest_role}.yaml"
    if not manifest_path.exists():
        return None, {}
    payload = parse_yaml_subset(manifest_path)
    if not isinstance(payload, dict):
        raise ValueError(f"Role-load manifest must decode to a mapping: {manifest_path}")
    return _repo_rel(change_root.parents[3], manifest_path), payload


def _matches_any_rule(path: str, rules: list[str]) -> bool:
    return any(path_matches_rule(path, rule) for rule in rules if rule)


def _change_scoped_read_paths(
    repo_root: Path,
    runtime_role: str,
    role_config: Mapping[str, Any],
    bundle_artifacts: list[str],
    bundle_candidate_artifact_rules: list[str],
    message_required_reads: list[str],
    change_context: Mapping[str, Any],
    role_load_payload: Mapping[str, Any],
) -> list[str]:
    affected_artifacts = list(change_context.get("affected_artifacts", []))
    affected_candidate_artifacts = list(change_context.get("affected_candidate_artifacts", []))
    affected_app_paths = list(change_context.get("affected_app_paths", []))

    declared_read_artifacts = _clean_declared_paths(_string_list(role_load_payload, "read_artifacts"))
    declared_candidate_artifacts = _clean_declared_paths(_string_list(role_load_payload, "candidate_artifacts"))
    declared_write_artifacts = _clean_declared_paths(_string_list(role_load_payload, "write_artifacts"))
    declared_verification_inputs = _clean_declared_paths(_string_list(role_load_payload, "verification_inputs"))
    declared_read_app_paths = _clean_declared_paths(_string_list(role_load_payload, "read_app_paths"))
    declared_write_app_paths = _clean_declared_paths(_string_list(role_load_payload, "write_app_paths"))

    explicit_message_artifacts = [
        path
        for path in message_required_reads
        if path.startswith("runs/current/artifacts/")
        or path.startswith("runs/current/changes/")
        or path.startswith("runs/current/evidence/")
    ]
    explicit_message_app_paths = [path for path in message_required_reads if path.startswith("app/")]

    reads: list[str] = []
    declared_artifacts = (
        declared_read_artifacts
        + declared_candidate_artifacts
        + declared_write_artifacts
        + declared_verification_inputs
    )
    if declared_artifacts:
        reads.extend(declared_artifacts)
    else:
        candidate_set = set(bundle_artifacts) | set(explicit_message_artifacts)
        default_artifact_rules = list(DEFAULT_CHANGE_ARTIFACT_RULES.get(runtime_role, ()))
        reads.extend(
            path
            for path in affected_artifacts
            if path in candidate_set and _matches_any_rule(path, default_artifact_rules)
        )
        role_writable_rules = _string_list(role_config, "writable")
        reads.extend(
            path
            for path in affected_artifacts
            if path not in reads and _matches_any_rule(path, role_writable_rules)
        )
        candidate_rules = bundle_candidate_artifact_rules or [
            rule
            for rule in role_writable_rules
            if rule.startswith("runs/current/changes/*/candidate/artifacts/")
        ]
        reads.extend(
            path
            for path in affected_candidate_artifacts
            if path not in reads and _matches_any_rule(path, candidate_rules)
        )

    declared_app_paths = declared_read_app_paths + declared_write_app_paths
    if declared_app_paths:
        reads.extend(declared_app_paths)
    else:
        app_rules = [rule for rule in _string_list(role_config, "writable") if rule.startswith("app/")]
        reads.extend(path for path in affected_app_paths if _matches_any_rule(path, app_rules))

    reads.extend(explicit_message_artifacts)
    reads.extend(explicit_message_app_paths)
    return _clean_declared_paths(reads)


def _narrow_change_writable_paths(
    writable: list[str],
    role_load_payload: Mapping[str, Any],
    *,
    bundle_payload: Mapping[str, Any] | None = None,
) -> list[str]:
    def artifact_family(path: str) -> str | None:
        parts = path.split("/")
        if path.startswith("runs/current/artifacts/") and len(parts) >= 4:
            return parts[3]
        if path.startswith("runs/current/changes/") and "/candidate/artifacts/" in path and len(parts) >= 7:
            return parts[6]
        return None

    candidate_artifacts = _clean_declared_paths(_string_list(role_load_payload, "candidate_artifacts"))
    write_artifacts = _clean_declared_paths(_string_list(role_load_payload, "write_artifacts"))
    write_app_paths = _clean_declared_paths(_string_list(role_load_payload, "write_app_paths"))
    verification_inputs = _clean_declared_paths(_string_list(role_load_payload, "verification_inputs"))
    bundle_name = str(bundle_payload.get("name", "")).strip().lower() if isinstance(bundle_payload, dict) else ""

    artifact_writes = candidate_artifacts + write_artifacts

    if not artifact_writes and not write_app_paths and not verification_inputs:
        return writable

    bundle_candidate_families: set[str] = set()
    if isinstance(bundle_payload, dict):
        bundle_candidate_rules = (
            _string_list(bundle_payload, "required_candidate_artifacts")
            + _string_list(bundle_payload, "writable_targets")
        )
        bundle_candidate_families = {
            artifact_family(rule)
            for rule in bundle_candidate_rules
            if rule.startswith("runs/current/changes/*/candidate/artifacts/")
        }
        bundle_candidate_families.discard(None)
    bundle_artifact_wildcard_rules = {
        rule
        for rule in (_string_list(bundle_payload, "writable_targets") if isinstance(bundle_payload, dict) else [])
        if rule.startswith("runs/current/artifacts/") and rule.endswith("/**")
    }
    preserve_bundle_review_family_rules = "review" in bundle_name

    artifact_families = {
        artifact_family(path)
        for path in artifact_writes
        if path.startswith("runs/current/artifacts/")
    }
    candidate_families = {
        artifact_family(path)
        for path in artifact_writes
        if path.startswith("runs/current/changes/") and "/candidate/artifacts/" in path
    }
    artifact_families.discard(None)
    candidate_families.discard(None)

    narrowed: list[str] = []
    for rule in writable:
        if candidate_families and rule.startswith("runs/current/artifacts/"):
            if artifact_family(rule) in bundle_candidate_families.intersection(candidate_families):
                continue
        if artifact_families and rule.startswith("runs/current/artifacts/"):
            if preserve_bundle_review_family_rules and rule in bundle_artifact_wildcard_rules:
                narrowed.append(rule)
                continue
            if artifact_family(rule) in artifact_families:
                continue
        if candidate_families and rule.startswith("runs/current/changes/*/candidate/artifacts/"):
            if artifact_family(rule) in candidate_families:
                continue
        if artifact_writes and (
            rule in artifact_writes
        ):
            continue
        if write_app_paths and rule.startswith("app/"):
            continue
        if verification_inputs and rule.startswith("runs/current/changes/*/verification/"):
            continue
        narrowed.append(rule)

    narrowed.extend(candidate_artifacts)
    narrowed.extend(write_artifacts)
    narrowed.extend(write_app_paths)
    narrowed.extend(verification_inputs)
    return narrowed


def _role_load_scope_is_populated(payload: Mapping[str, Any]) -> bool:
    declared_paths = (
        _clean_declared_paths(_string_list(payload, "read_artifacts"))
        + _clean_declared_paths(_string_list(payload, "candidate_artifacts"))
        + _clean_declared_paths(_string_list(payload, "write_artifacts"))
        + _clean_declared_paths(_string_list(payload, "read_app_paths"))
        + _clean_declared_paths(_string_list(payload, "write_app_paths"))
        + _clean_declared_paths(_string_list(payload, "verification_inputs"))
    )
    return bool(declared_paths)


def _path_is_invalid_placeholder(path: str) -> bool:
    normalized = path.strip()
    if not normalized:
        return True
    if normalized in {"[]", "{}"}:
        return True
    if normalized.endswith("/[]") or "/[]/" in normalized:
        return True
    return _is_placeholder_value(normalized)


def collect_packet_health_issues(
    repo_root: Path,
    runtime_role: str,
    packet: Mapping[str, Any],
    *,
    explicit_phase: str | None = None,
) -> list[str]:
    change_context = packet.get("change_context")
    if not isinstance(change_context, dict):
        return []

    current_phase = str(explicit_phase or change_context.get("current_phase", "")).strip()
    if not any(current_phase.startswith(prefix) for prefix in STRICT_ROLE_LOAD_PHASE_PREFIXES):
        return []

    issues: list[str] = []
    role_load_relpath = packet.get("role_load_manifest")
    role_load_payload = packet.get("role_load_payload")
    if not isinstance(role_load_payload, dict):
        role_load_payload = {}

    if not isinstance(role_load_relpath, str) or not role_load_relpath.strip():
        issues.append(
            f"missing populated role-load manifest for {runtime_role} in {current_phase}; "
            "late change-run dispatch must not rely on fallback affected-scope routing"
        )
    else:
        if _payload_contains_placeholder(role_load_payload):
            issues.append(
                f"role-load manifest still contains template placeholder text: {role_load_relpath}"
            )
        if not _role_load_scope_is_populated(role_load_payload):
            issues.append(
                f"role-load manifest does not declare any concrete read/write scope: {role_load_relpath}"
            )

    read_paths = packet.get("read_paths", [])
    if isinstance(read_paths, list):
        for read_path in read_paths:
            if not isinstance(read_path, str):
                continue
            if _path_is_invalid_placeholder(read_path):
                issues.append(f"resolved read path is still a placeholder or invalid token: {read_path}")

    return issues


def resolve_read_packet(
    repo_root: Path,
    runtime_role: str,
    *,
    message_required_reads: list[str] | None = None,
    explicit_task_bundle: str | None = None,
    explicit_phase: str | None = None,
    include_message_path: Path | None = None,
) -> dict[str, Any]:
    role_config = resolve_role_config(repo_root, runtime_role)
    change_context = _active_change_context(repo_root)
    summary_path, bundle_path = resolve_phase_bundle(
        repo_root,
        runtime_role,
        explicit_task_bundle=explicit_task_bundle,
        explicit_phase=explicit_phase,
        message_required_reads=message_required_reads,
    )

    read_paths: list[str] = ["playbook/index.md"]
    read_paths.extend(_string_list(role_config, "always_load"))
    read_paths.extend(
        [
            "runs/current/artifacts/architecture/capability-profile.md",
            "runs/current/artifacts/architecture/load-plan.md",
        ]
    )
    if summary_path:
        read_paths.append(summary_path)

    bundle_payload: Mapping[str, Any] = {}
    bundle_artifacts: list[str] = []
    bundle_candidate_artifact_rules: list[str] = []
    if bundle_path:
        read_paths.append(bundle_path)
        bundle_payload = parse_yaml_subset(repo_root / bundle_path)
        if not isinstance(bundle_payload, dict):
            raise ValueError(f"Task bundle must decode to a mapping: {bundle_path}")
        read_paths.extend(_string_list(bundle_payload, "always_load"))
        read_paths.extend(_string_list(bundle_payload, "required_phase"))
        bundle_artifacts.extend(_string_list(bundle_payload, "required_artifacts"))
        bundle_candidate_artifact_rules.extend(_string_list(bundle_payload, "required_candidate_artifacts"))

        conditional = bundle_payload.get("conditional_artifacts", {})
        if isinstance(conditional, dict):
            enabled_features = enabled_features_for_role(repo_root, runtime_role)
            for condition, paths in conditional.items():
                if not isinstance(condition, str) or not _condition_active(repo_root, condition, enabled_features):
                    continue
                if isinstance(paths, list):
                    bundle_artifacts.extend(item for item in paths if isinstance(item, str))
                elif isinstance(paths, str):
                    bundle_artifacts.append(paths)

    role_load_relpath: str | None = None
    role_load_payload: Mapping[str, Any] = {}
    external_reference_relpath: str | None = None
    external_reference_payload: Mapping[str, Any] = {}
    if change_context is not None:
        change_root = Path(change_context["change_root"])
        for name in (
            "request.md",
            "classification.yaml",
            "impact-manifest.yaml",
            "affected-artifacts.md",
            "affected-candidate-artifacts.md",
            "affected-app-paths.md",
            "reopened-gates.md",
        ):
            path = change_root / name
            if path.exists():
                read_paths.append(_repo_rel(repo_root, path))

        role_load_relpath, role_load_payload = _load_role_load_manifest(change_root, runtime_role)
        if role_load_relpath:
            read_paths.append(role_load_relpath)

        external_reference_relpath, external_reference_payload = _load_external_reference_manifest(change_root)
        if external_reference_relpath:
            read_paths.append(external_reference_relpath)
            read_paths.extend(
                _external_reference_read_paths(
                    repo_root,
                    runtime_role,
                    change_root,
                    external_reference_payload,
                )
            )

        read_paths.extend(
            _change_scoped_read_paths(
                repo_root,
                runtime_role,
                role_config,
                bundle_artifacts,
                bundle_candidate_artifact_rules,
                message_required_reads or [],
                change_context,
                role_load_payload,
            )
        )
    else:
        read_paths.extend(bundle_artifacts)

    for path in message_required_reads or []:
        if isinstance(path, str):
            read_paths.append(path)

    if include_message_path is not None:
        read_paths.append(_repo_rel(repo_root, include_message_path))

    seen: set[str] = set()
    deduped_reads: list[str] = []
    for path in read_paths:
        if not path or path in seen:
            continue
        seen.add(path)
        deduped_reads.append(path)

    return {
        "phase_summary": summary_path,
        "task_bundle": bundle_path,
        "task_bundle_payload": bundle_payload,
        "change_context": change_context,
        "role_load_manifest": role_load_relpath,
        "role_load_payload": role_load_payload,
        "external_reference_manifest": external_reference_relpath,
        "external_reference_payload": external_reference_payload,
        "read_paths": deduped_reads,
    }


def resolve_writable_paths(
    repo_root: Path,
    runtime_role: str,
    *,
    explicit_task_bundle: str | None = None,
    explicit_phase: str | None = None,
    message_required_reads: list[str] | None = None,
    message_headers: Mapping[str, Any] | None = None,
    message_sections: Mapping[str, Any] | None = None,
) -> list[str]:
    role_config = resolve_role_config(repo_root, runtime_role)
    packet = resolve_read_packet(
        repo_root,
        runtime_role,
        message_required_reads=message_required_reads,
        explicit_task_bundle=explicit_task_bundle,
        explicit_phase=explicit_phase,
    )
    writable = _string_list(role_config, "writable")

    bundle_payload = packet.get("task_bundle_payload", {})
    if isinstance(bundle_payload, dict):
        writable.extend(_string_list(bundle_payload, "writable_targets"))

    role_load_payload = packet.get("role_load_payload", {})
    if isinstance(role_load_payload, dict):
        writable = _narrow_change_writable_paths(
            writable,
            role_load_payload,
            bundle_payload=bundle_payload if isinstance(bundle_payload, dict) else None,
        )

    writable.extend(resolve_message_scoped_writable_paths(repo_root, runtime_role, message_headers, message_sections))

    writable.append("runs/current/role-state/*/inbox/*.md")
    for role_state_dir in role_state_dir_names(runtime_role):
        writable.extend(
            [
                f"runs/current/role-state/{role_state_dir}/inflight/*.md",
                f"runs/current/role-state/{role_state_dir}/processed/*.md",
                f"runs/current/role-state/{role_state_dir}/context.md",
            ]
        )

    seen: set[str] = set()
    deduped: list[str] = []
    for path in writable:
        if not path or path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


def resolve_forbidden_paths(repo_root: Path, runtime_role: str) -> list[str]:
    role_config = resolve_role_config(repo_root, runtime_role)
    forbidden = _string_list(role_config, "cannot_write")

    seen: set[str] = set()
    deduped: list[str] = []
    for path in forbidden:
        if not path or path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped
