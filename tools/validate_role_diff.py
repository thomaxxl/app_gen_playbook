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
from routing_resolver import resolve_writable_paths


def allowed_prefixes(
    repo_root: Path,
    runtime_role: str,
    *,
    message_path: Path | None = None,
) -> list[str]:
    required_reads: list[str] = []
    explicit_task_bundle: str | None = None
    explicit_phase: str | None = None

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
    )


def ignored_prefixes(ignore_runtime_roles: list[str]) -> list[str]:
    prefixes: list[str] = []
    for runtime_role in ignore_runtime_roles:
        prefixes.extend(list(owned_prefixes(runtime_role)))
    return prefixes


def is_allowed_change(
    repo_root: Path,
    runtime_role: str,
    relative_path: str,
    ignore_runtime_roles: list[str],
    *,
    message_path: Path | None = None,
) -> bool:
    if relative_path.startswith("runs/current/role-state/") and relative_path.endswith(".md"):
        if "/inbox/" in relative_path:
            return True

    valid_prefixes = allowed_prefixes(repo_root, runtime_role, message_path=message_path) + ignored_prefixes(ignore_runtime_roles)
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
) -> int:
    before = read_json(snapshot_path)
    if not isinstance(before, dict):
        raise SystemExit(f"error: invalid snapshot payload in {snapshot_path}")

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
        )
    ]
    if evidence_out is not None:
        evidence_out.parent.mkdir(parents=True, exist_ok=True)
        evidence_lines = [
            f"runtime_role: {runtime_role}",
            f"changed_files: {len(changed)}",
            f"ignored_runtime_roles: {', '.join(ignore_runtime_roles) if ignore_runtime_roles else '(none)'}",
            "",
            "## Changed files",
        ]
        evidence_lines.extend(f"- {path}" for path in changed)
        evidence_lines.extend(["", "## Forbidden files"])
        evidence_lines.extend(f"- {path}" for path in violations)
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
    )


if __name__ == "__main__":
    raise SystemExit(main())
