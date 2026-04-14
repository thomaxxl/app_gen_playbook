#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from orchestrator_common import (
    owned_prefixes,
    path_matches_rule,
    parse_message_headers,
    parse_message_sections,
    read_json,
    resolve_repo_root,
    snapshot_repo_files,
    write_json,
)
from routing_resolver import resolve_forbidden_paths, resolve_writable_paths
from routing_resolver import resolve_message_scoped_writable_paths


def allowed_prefixes(
    repo_root: Path,
    runtime_role: str,
    *,
    message_path: Path | None = None,
) -> list[str]:
    required_reads: list[str] = []
    explicit_task_bundle: str | None = None
    explicit_phase: str | None = None
    headers: dict[str, str] = {}
    sections: dict[str, list[str] | str] = {}

    if message_path is not None and message_path.exists():
        message_text = message_path.read_text(encoding="utf-8")
        headers = parse_message_headers(message_text)
        sections = parse_message_sections(message_text, headers=headers)
        required_reads = [item for item in sections.get("required reads", []) if isinstance(item, str)]
        explicit_task_bundle = headers.get("taskbundle") or headers.get("task_bundle")
        explicit_phase = headers.get("phase")

    return resolve_writable_paths(
        repo_root,
        runtime_role,
        explicit_task_bundle=explicit_task_bundle,
        explicit_phase=explicit_phase,
        message_required_reads=required_reads,
        message_headers=headers,
        message_sections=sections,
    )


def scoped_write_exceptions(
    repo_root: Path,
    runtime_role: str,
    *,
    message_path: Path | None = None,
) -> list[str]:
    if message_path is None or not message_path.exists():
        return []
    message_text = message_path.read_text(encoding="utf-8")
    headers = parse_message_headers(message_text)
    sections = parse_message_sections(message_text, headers=headers)
    return resolve_message_scoped_writable_paths(repo_root, runtime_role, headers, sections)


def ignored_prefixes(ignore_runtime_roles: list[str]) -> list[str]:
    prefixes: list[str] = []
    for runtime_role in ignore_runtime_roles:
        prefixes.extend(list(owned_prefixes(runtime_role)))
    return prefixes


def _path_variants(path: Path) -> list[Path]:
    variants = [path]
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    if resolved != path:
        variants.append(resolved)
    return variants


def change_within_turn_roots(repo_root: Path, relative_path: str, turn_roots: list[Path]) -> bool:
    if not turn_roots:
        return True

    target = repo_root / relative_path
    target_variants = _path_variants(target)
    normalized_roots: list[Path] = []
    for root in turn_roots:
        normalized_roots.extend(_path_variants(root))

    for candidate in target_variants:
        for root in normalized_roots:
            if candidate == root or candidate.is_relative_to(root):
                return True
    return False


def is_allowed_change(
    repo_root: Path,
    runtime_role: str,
    relative_path: str,
    ignore_runtime_roles: list[str],
    *,
    message_path: Path | None = None,
    turn_roots: list[Path] | None = None,
    allowed_write_rules: list[str] | None = None,
    forbidden_write_rules: list[str] | None = None,
) -> bool:
    if turn_roots is not None and not change_within_turn_roots(repo_root, relative_path, turn_roots):
        return True

    if relative_path.startswith("runs/current/role-state/") and relative_path.endswith(".md"):
        if "/inbox/" in relative_path:
            return True

    exception_rules = scoped_write_exceptions(repo_root, runtime_role, message_path=message_path)
    if any(path_matches_rule(relative_path, rule) for rule in exception_rules):
        return True

    forbidden_prefixes = (
        list(forbidden_write_rules)
        if forbidden_write_rules is not None
        else resolve_forbidden_paths(repo_root, runtime_role)
    )
    if any(path_matches_rule(relative_path, prefix) for prefix in forbidden_prefixes):
        return False

    valid_prefixes = (
        list(allowed_write_rules)
        if allowed_write_rules is not None
        else allowed_prefixes(repo_root, runtime_role, message_path=message_path)
    ) + ignored_prefixes(ignore_runtime_roles)
    return any(path_matches_rule(relative_path, prefix) for prefix in valid_prefixes)


def snapshot_command(repo_root: Path, output_path: Path) -> int:
    snapshot = snapshot_repo_files(repo_root)
    write_json(output_path, snapshot)
    print(output_path)
    return 0


def validate_command(
    repo_root: Path,
    runtime_role: str,
    snapshot_path: Path,
    evidence_out: Path | None,
    ignore_runtime_roles: list[str],
    message_path: Path | None,
    turn_roots: list[Path],
    scope_artifact: Path | None,
    allowed_write_rules: list[str],
    forbidden_write_rules: list[str],
) -> int:
    before = read_json(snapshot_path)
    if not isinstance(before, dict):
        raise SystemExit(f"error: invalid snapshot payload in {snapshot_path}")

    resolved_scope_payload: dict[str, object] = {}
    if scope_artifact is not None:
        payload = read_json(scope_artifact)
        if isinstance(payload, dict):
            resolved_scope_payload = payload
            if not allowed_write_rules:
                value = payload.get("write_rules", [])
                if isinstance(value, list):
                    allowed_write_rules = [item for item in value if isinstance(item, str)]
            if not forbidden_write_rules:
                value = payload.get("forbidden_rules", [])
                if isinstance(value, list):
                    forbidden_write_rules = [item for item in value if isinstance(item, str)]
            if not turn_roots:
                value = payload.get("write_roots", [])
                if isinstance(value, list):
                    turn_roots = [Path(item).resolve() for item in value if isinstance(item, str)]

    after = snapshot_repo_files(repo_root)
    before_paths = set(before)
    after_paths = set(after)

    changed: list[str] = []
    for path in sorted(before_paths | after_paths):
        if before.get(path) != after.get(path):
            changed.append(path)

    violations = [
        path
        for path in changed
        if not is_allowed_change(
            repo_root,
            runtime_role,
            path,
            ignore_runtime_roles,
            message_path=message_path,
            turn_roots=turn_roots,
            allowed_write_rules=allowed_write_rules or None,
            forbidden_write_rules=forbidden_write_rules or None,
        )
    ]
    external_changes = [
        path
        for path in changed
        if turn_roots and not change_within_turn_roots(repo_root, path, turn_roots)
    ]
    if evidence_out is not None:
        evidence_out.parent.mkdir(parents=True, exist_ok=True)
        evidence_lines = [
            f"runtime_role: {runtime_role}",
            f"changed_files: {len(changed)}",
            f"ignored_runtime_roles: {', '.join(ignore_runtime_roles) if ignore_runtime_roles else '(none)'}",
            f"scope_artifact: {scope_artifact if scope_artifact else '(none)'}",
            "",
            "## Resolved write rules",
        ]
        evidence_lines.extend(f"- {path}" for path in (allowed_write_rules or ["(resolved at validation time)"]))
        evidence_lines.extend(["", "## Forbidden write rules"])
        evidence_lines.extend(f"- {path}" for path in (forbidden_write_rules or ["(resolved at validation time)"]))
        evidence_lines.extend(["", "## Write roots"])
        evidence_lines.extend(f"- {path}" for path in ([str(item) for item in turn_roots] or ["(none)"]))
        evidence_lines.extend([
            "",
            "## Changed files",
        ])
        evidence_lines.extend(f"- {path}" for path in changed)
        evidence_lines.extend(["", "## External concurrent changes"])
        evidence_lines.extend(f"- {path}" for path in external_changes)
        evidence_lines.extend(["", "## Forbidden files"])
        evidence_lines.extend(f"- {path}" for path in violations)
        if resolved_scope_payload:
            evidence_lines.extend(["", "## Resolved scope payload"])
            evidence_lines.extend(f"- {key}: {value}" for key, value in sorted(resolved_scope_payload.items()))
        evidence_out.write_text("\n".join(evidence_lines) + "\n", encoding="utf-8")

    if violations:
        print("forbidden writes detected:")
        for path in violations:
            print(f"- {path}")
        return 1

    if changed:
        print("validated changed files:")
        for path in changed:
            print(f"- {path}")
    else:
        print("no file changes detected")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_parser = subparsers.add_parser("snapshot")
    snapshot_parser.add_argument("--repo-root", required=True)
    snapshot_parser.add_argument("--output", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--repo-root", required=True)
    validate_parser.add_argument("--runtime-role", required=True)
    validate_parser.add_argument("--snapshot", required=True)
    validate_parser.add_argument("--evidence-out")
    validate_parser.add_argument("--ignore-runtime-role", action="append", default=[])
    validate_parser.add_argument("--message")
    validate_parser.add_argument("--turn-root", action="append", default=[])
    validate_parser.add_argument("--scope-artifact")
    validate_parser.add_argument("--allowed-write-rule", action="append", default=[])
    validate_parser.add_argument("--forbidden-write-rule", action="append", default=[])

    args = parser.parse_args()

    if args.command == "snapshot":
        repo_root = resolve_repo_root(args.repo_root)
        return snapshot_command(repo_root, Path(args.output).resolve())

    repo_root = resolve_repo_root(args.repo_root)
    return validate_command(
        repo_root,
        args.runtime_role,
        Path(args.snapshot).resolve(),
        Path(args.evidence_out).resolve() if args.evidence_out else None,
        list(args.ignore_runtime_role),
        Path(args.message).resolve() if args.message else None,
        [Path(item).resolve() for item in args.turn_root],
        Path(args.scope_artifact).resolve() if args.scope_artifact else None,
        list(args.allowed_write_rule),
        list(args.forbidden_write_rule),
    )


if __name__ == "__main__":
    raise SystemExit(main())
