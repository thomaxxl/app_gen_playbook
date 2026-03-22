from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

from orchestrator_common import relpath


def parse_yaml_subset(path: Path) -> Any:
    lines = path.read_text(encoding="utf-8").splitlines()
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]

    for index, raw_line in enumerate(lines):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        text = raw_line.strip()

        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]

        if text.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"Invalid list item in {path}: {raw_line}")
            parent.append(text[2:].strip())
            continue

        if ":" not in text:
            raise ValueError(f"Invalid mapping entry in {path}: {raw_line}")

        key, remainder = text.split(":", 1)
        key = key.strip()
        remainder = remainder.strip()

        if remainder:
            if not isinstance(parent, dict):
                raise ValueError(f"Invalid scalar parent in {path}: {raw_line}")
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

    if bundle_candidates:
        return None, bundle_candidates[0]
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
    if bundle_path:
        read_paths.append(bundle_path)
        bundle_payload = parse_yaml_subset(repo_root / bundle_path)
        if not isinstance(bundle_payload, dict):
            raise ValueError(f"Task bundle must decode to a mapping: {bundle_path}")
        read_paths.extend(_string_list(bundle_payload, "always_load"))
        read_paths.extend(_string_list(bundle_payload, "required_phase"))
        read_paths.extend(_string_list(bundle_payload, "required_artifacts"))

        conditional = bundle_payload.get("conditional_artifacts", {})
        if isinstance(conditional, dict):
            enabled_features = enabled_features_for_role(repo_root, runtime_role)
            for condition, paths in conditional.items():
                if not isinstance(condition, str) or not _condition_active(repo_root, condition, enabled_features):
                    continue
                if isinstance(paths, list):
                    read_paths.extend(item for item in paths if isinstance(item, str))
                elif isinstance(paths, str):
                    read_paths.append(paths)

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
        "read_paths": deduped_reads,
    }


def resolve_writable_paths(
    repo_root: Path,
    runtime_role: str,
    *,
    explicit_task_bundle: str | None = None,
    explicit_phase: str | None = None,
    message_required_reads: list[str] | None = None,
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

    writable.extend(
        [
            "runs/current/role-state/*/inbox/*.md",
            "runs/current/role-state/*/processed/*.md",
            "runs/current/role-state/*/context.md",
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
