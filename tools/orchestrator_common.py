from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Iterable


CORE_DISPLAY_ROLES = ("product-manager", "architect", "frontend", "backend")

DISPLAY_TO_RUNTIME = {
    "product-manager": "product_manager",
    "architect": "architect",
    "frontend": "frontend",
    "backend": "backend",
    "deployment": "deployment",
    "devops": "deployment",
}

DISPLAY_TO_ROLE_FILE = {
    "product-manager": "playbook/roles/product-manager.md",
    "architect": "playbook/roles/architect.md",
    "frontend": "playbook/roles/frontend.md",
    "backend": "playbook/roles/backend.md",
    "deployment": "playbook/roles/devops.md",
    "devops": "playbook/roles/devops.md",
}

RUNTIME_TO_DISPLAY = {
    "product_manager": "product-manager",
    "architect": "architect",
    "frontend": "frontend",
    "backend": "backend",
    "deployment": "deployment",
}

ARTIFACT_AREA_BY_ROLE = {
    "product_manager": "product",
    "architect": "architecture",
    "frontend": "ux",
    "backend": "backend-design",
    "deployment": "devops",
}

RUN_ARTIFACT_TEMPLATE_DIRS = {
    "product": "specs/product",
    "architecture": "specs/architecture",
    "ux": "specs/ux",
    "backend-design": "specs/backend-design",
}

PHASE5_READY_PHASES = {
    "phase-1-product-definition",
    "phase-2-architecture-contract",
    "phase-3-ux-and-interaction-design",
    "phase-4-backend-design-and-rules-mapping",
}

ROLE_OWNED_PREFIXES = {
    "product_manager": (
        "runs/current/artifacts/product/",
        "runs/current/role-state/product_manager/",
        "app/BUSINESS_RULES.md",
    ),
    "architect": (
        "runs/current/artifacts/architecture/",
        "runs/current/role-state/architect/",
        "app/README.md",
    ),
    "frontend": (
        "runs/current/artifacts/ux/",
        "runs/current/role-state/frontend/",
        "app/frontend/",
    ),
    "backend": (
        "runs/current/artifacts/backend-design/",
        "runs/current/role-state/backend/",
        "app/backend/",
        "app/rules/",
        "app/reference/admin.yaml",
    ),
    "deployment": (
        "runs/current/artifacts/devops/",
        "runs/current/role-state/deployment/",
        "app/.gitignore",
        "app/Dockerfile",
        "app/docker-compose.yml",
        "app/nginx.conf",
        "app/entrypoint.sh",
        "app/install.sh",
        "app/run.sh",
    ),
}

EXCLUDED_DIR_NAMES = {
    ".git",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "playwright-report",
    "test-results",
    ".deps",
    ".venv",
    "venv",
    "env",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    ".vite",
}

EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".tsbuildinfo",
}

EXCLUDED_ROOT_DIRS = {
    "app.cmdb",
}


def resolve_repo_root(path: str | Path) -> Path:
    repo_root = Path(path).resolve()
    if not (repo_root / ".git").exists():
        raise SystemExit(f"error: not a git repo root: {repo_root}")
    return repo_root


def relpath(path: Path, repo_root: Path) -> str:
    repo_root_abs = Path(os.path.abspath(repo_root))
    path_abs = Path(os.path.abspath(path))

    if os.path.commonpath((str(repo_root_abs), str(path_abs))) != str(repo_root_abs):
        raise ValueError(f"{path_abs!s} is not in the subpath of {repo_root_abs!s}")

    return path_abs.relative_to(repo_root_abs).as_posix()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def should_ignore_path(path: Path, repo_root: Path) -> bool:
    relative = relpath(path, repo_root)
    parts = relative.split("/")

    if parts[0] in EXCLUDED_ROOT_DIRS:
        return True

    if relative.startswith("runs/current/evidence/orchestrator/"):
        return True

    if relative.startswith("runs/current/orchestrator/"):
        return True

    if any(part in EXCLUDED_DIR_NAMES for part in parts[:-1]):
        return True

    if path.suffix in EXCLUDED_SUFFIXES:
        return True

    if path.is_file() and path.name in {".DS_Store", "Thumbs.db"}:
        return True

    return False


def snapshot_repo_files(repo_root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}

    for root, dirs, files in os.walk(repo_root):
        root_path = Path(root)
        dirs[:] = [
            directory
            for directory in dirs
            if not should_ignore_path(root_path / directory, repo_root)
        ]

        for filename in files:
            path = root_path / filename
            if should_ignore_path(path, repo_root) or not path.is_file():
                continue
            snapshot[relpath(path, repo_root)] = hash_file(path)

    return dict(sorted(snapshot.items()))


def parse_metadata_block(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return {}

    metadata: dict[str, object] = {}
    current_key: str | None = None
    index = 0
    delimited = False

    if lines[0].strip() == "---":
        delimited = True
        index = 1

    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()

        if delimited and stripped == "---":
            break

        if not delimited and (not stripped or stripped.startswith("#")):
            break

        key_match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", raw_line)
        if key_match:
            current_key = key_match.group(1)
            value = key_match.group(2).strip()
            if value:
                metadata[current_key] = value
                current_key = None
            else:
                metadata[current_key] = []
            index += 1
            continue

        list_match = re.match(r"^\s*-\s+(.*)$", raw_line)
        if list_match and current_key:
            current_value = metadata.setdefault(current_key, [])
            if isinstance(current_value, list):
                current_value.append(list_match.group(1).strip())
            index += 1
            continue

        break

    return metadata


def iter_required_artifact_templates(repo_root: Path) -> Iterable[tuple[str, Path]]:
    for artifact_dir, relative_template_dir in RUN_ARTIFACT_TEMPLATE_DIRS.items():
        template_dir = repo_root / relative_template_dir
        for template_path in sorted(template_dir.glob("*.md")):
            if template_path.name == "README.md":
                continue
            metadata = parse_metadata_block(template_path)
            if metadata.get("status") == "stub" and "owner" in metadata:
                yield artifact_dir, template_path


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def owned_prefixes(runtime_role: str) -> tuple[str, ...]:
    try:
        return ROLE_OWNED_PREFIXES[runtime_role]
    except KeyError as exc:
        raise SystemExit(f"error: unknown runtime role: {runtime_role}") from exc
