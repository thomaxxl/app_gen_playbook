#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from orchestrator_common import read_json, relpath, resolve_repo_root, snapshot_repo_files, write_json


def allowed_prefixes(runtime_role: str) -> list[str]:
    role_dir = f"runs/current/role-state/{runtime_role}/"
    prefixes = [
        f"runs/current/evidence/",
        f"runs/current/role-state/{runtime_role}/",
        "runs/current/role-state/",
    ]

    if runtime_role == "product_manager":
        prefixes.extend(
            [
                "runs/current/artifacts/product/",
                "app/BUSINESS_RULES.md",
            ]
        )
    elif runtime_role == "architect":
        prefixes.extend(["runs/current/artifacts/architecture/"])
    elif runtime_role == "frontend":
        prefixes.extend(
            [
                "runs/current/artifacts/ux/",
                "app/frontend/",
                "app/reference/admin.yaml",
                "app/README.md",
            ]
        )
    elif runtime_role == "backend":
        prefixes.extend(
            [
                "runs/current/artifacts/backend-design/",
                "app/backend/",
                "app/reference/admin.yaml",
            ]
        )
    elif runtime_role == "deployment":
        prefixes.extend(
            [
                "runs/current/artifacts/devops/",
                "app/Dockerfile",
                "app/docker-compose.yml",
                "app/nginx.conf",
                "app/entrypoint.sh",
                "app/install.sh",
                "app/run.sh",
                "app/README.md",
            ]
        )

    return prefixes


def is_allowed_change(runtime_role: str, relative_path: str) -> bool:
    if relative_path.startswith("runs/current/role-state/") and relative_path.endswith(".md"):
        if "/inbox/" in relative_path:
            return True
    return any(
        relative_path == prefix.rstrip("/") or relative_path.startswith(prefix)
        for prefix in allowed_prefixes(runtime_role)
    )


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

    violations = [path for path in changed if not is_allowed_change(runtime_role, path)]
    if evidence_out is not None:
        evidence_out.parent.mkdir(parents=True, exist_ok=True)
        evidence_lines = [
            f"runtime_role: {runtime_role}",
            f"changed_files: {len(changed)}",
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
    )


if __name__ == "__main__":
    raise SystemExit(main())
