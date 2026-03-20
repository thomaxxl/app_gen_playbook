from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from fnmatch import fnmatch
from typing import Iterable, Mapping


CORE_DISPLAY_ROLES = ("product-manager", "architect", "frontend", "backend", "qa")

DISPLAY_TO_RUNTIME = {
    "product-manager": "product_manager",
    "architect": "architect",
    "frontend": "frontend",
    "backend": "backend",
    "qa": "qa",
    "ceo": "ceo",
    "deployment": "deployment",
    "devops": "deployment",
}

DISPLAY_TO_ROLE_FILE = {
    "product-manager": "playbook/roles/product-manager.md",
    "architect": "playbook/roles/architect.md",
    "frontend": "playbook/roles/frontend.md",
    "backend": "playbook/roles/backend.md",
    "qa": "playbook/roles/qa.md",
    "ceo": "playbook/roles/ceo.md",
    "deployment": "playbook/roles/devops.md",
    "devops": "playbook/roles/devops.md",
}

RUNTIME_TO_DISPLAY = {
    "product_manager": "product-manager",
    "architect": "architect",
    "frontend": "frontend",
    "backend": "backend",
    "qa": "qa",
    "ceo": "ceo",
    "deployment": "deployment",
}

ROLE_STATE_DIR_BY_RUNTIME = {
    "product_manager": "product_manager",
    "architect": "architect",
    "frontend": "frontend",
    "backend": "backend",
    "qa": "qa",
    "ceo": "ceo",
    "deployment": "devops",
}

ROLE_STATE_LEGACY_DIRS = {
    "deployment": ("deployment",),
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
        "runs/current/remarks.md",
        "runs/current/notes.md",
        "runs/current/artifacts/product/",
        "runs/current/evidence/ui-previews/manifest.md",
        "runs/current/role-state/product_manager/",
        "runs/current/changes/*/request.md",
        "runs/current/changes/*/classification.yaml",
        "runs/current/changes/*/affected-artifacts.md",
        "runs/current/changes/*/affected-app-paths.md",
        "runs/current/changes/*/reopened-gates.md",
        "runs/current/changes/*/candidate/artifacts/product/**",
        "runs/current/changes/*/promotion.yaml",
        "app/BUSINESS_RULES.md",
        "app/docs/playbook-baseline/current/**",
        "app/docs/change-history/**",
    ),
    "architect": (
        "runs/current/remarks.md",
        "runs/current/notes.md",
        "runs/current/artifacts/architecture/",
        "runs/current/role-state/architect/",
        "runs/current/changes/*/impact-manifest.yaml",
        "runs/current/changes/*/role-loads/**",
        "runs/current/changes/*/candidate/artifacts/architecture/**",
        "runs/current/changes/*/verification/**",
        "app/README.md",
    ),
    "frontend": (
        "runs/current/remarks.md",
        "runs/current/notes.md",
        "runs/current/artifacts/ux/",
        "runs/current/evidence/frontend-usability.md",
        "runs/current/evidence/ui-previews/**",
        "runs/current/role-state/frontend/",
        "runs/current/changes/*/candidate/artifacts/ux/**",
        "runs/current/changes/*/verification/**",
        "app/frontend/",
    ),
    "backend": (
        "runs/current/remarks.md",
        "runs/current/notes.md",
        "runs/current/artifacts/backend-design/",
        "runs/current/role-state/backend/",
        "runs/current/changes/*/candidate/artifacts/backend-design/**",
        "runs/current/changes/*/verification/**",
        "app/backend/",
        "app/rules/",
        "app/reference/admin.yaml",
    ),
    "qa": (
        "runs/current/remarks.md",
        "runs/current/notes.md",
        "runs/current/evidence/qa-delivery-review.md",
        "runs/current/role-state/qa/",
    ),
    "deployment": (
        "runs/current/remarks.md",
        "runs/current/notes.md",
        "runs/current/artifacts/devops/",
        "runs/current/role-state/devops/",
        "runs/current/role-state/deployment/",
        "runs/current/changes/*/candidate/artifacts/devops/**",
        "runs/current/changes/*/verification/**",
        "app/.gitignore",
        "app/Dockerfile",
        "app/docker-compose.yml",
        "app/nginx.conf",
        "app/entrypoint.sh",
        "app/install.sh",
        "app/run.sh",
    ),
    "ceo": (
        "runs/current/artifacts/",
        "runs/current/changes/",
        "runs/current/role-state/",
        "runs/current/remarks.md",
        "runs/current/notes.md",
        "runs/current/orchestrator/delivery-approved.md",
        "runs/current/orchestrator/ceo-progress-followup-requested.md",
        "runs/current/orchestrator/operator-action-required.md",
        "runs/current/orchestrator/pause-requested.md",
        "runs/current/evidence/ceo-delivery-validation.md",
        "runs/current/evidence/contract-samples.md",
        "app/",
        "playbook/",
        "scripts/",
        "tools/",
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

MESSAGE_SECTION_TITLES = (
    "required reads",
    "requested outputs",
    "dependencies",
    "gate status",
    "implementation evidence",
    "blocking issues",
    "notes",
)

MESSAGE_SECTION_ALIASES = {
    "requested outputs completed": "requested outputs",
}

MESSAGE_FIELD_ALIASES = {
    "from": ("from", "sender"),
    "to": ("to", "receiver"),
    "gate_status": ("gate_status", "gate-status", "gate status"),
}


def resolve_repo_root(path: str | Path) -> Path:
    repo_root = Path(path).resolve()
    if not (repo_root / ".git").exists():
        raise SystemExit(f"error: not a git repo root: {repo_root}")
    return repo_root


def normalize_message_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.strip().lower())


def canonical_message_section_title(normalized: str) -> str | None:
    if normalized in MESSAGE_SECTION_TITLES:
        return normalized
    return MESSAGE_SECTION_ALIASES.get(normalized)


def parse_message_headers(message_text: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    lines = message_text.splitlines()
    index = 0
    delimited = bool(lines and lines[0].strip() == "---")

    if delimited:
        index = 1

    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()

        if delimited and stripped == "---":
            break
        if stripped.startswith("##"):
            break
        if not stripped:
            if headers:
                break
            index += 1
            continue

        key_match = re.match(r"^([A-Za-z][A-Za-z0-9_ -]*):\s*(.*)$", raw_line)
        if not key_match:
            if headers:
                break
            index += 1
            continue

        headers[normalize_message_key(key_match.group(1))] = key_match.group(2).strip()
        index += 1

    return headers


def message_header_field(headers: Mapping[str, str], field_name: str) -> str:
    aliases = MESSAGE_FIELD_ALIASES.get(field_name, (field_name,))
    for alias in aliases:
        value = headers.get(normalize_message_key(alias), "").strip()
        if value:
            return value
    return ""


def parse_message_sections(
    message_text: str,
    *,
    headers: Mapping[str, str] | None = None,
) -> dict[str, list[str] | str]:
    if headers is None:
        headers = parse_message_headers(message_text)

    lines = message_text.splitlines()
    sections: dict[str, list[str]] = {title: [] for title in MESSAGE_SECTION_TITLES}
    current_section: str | None = None

    for raw_line in lines:
        line = raw_line.strip()
        normalized = re.sub(r"^[#\-\*\s]+", "", line).rstrip(":").strip().lower()
        section_title = canonical_message_section_title(normalized)
        if section_title is not None:
            current_section = section_title
            continue
        if line.startswith("#"):
            current_section = None
            continue
        if current_section is None or not line:
            continue

        bullet_match = re.match(r"^[-*]\s+(.*)$", line)
        numbered_match = re.match(r"^\d+\.\s+(.*)$", line)
        if bullet_match:
            sections[current_section].append(bullet_match.group(1).strip())
        elif numbered_match:
            sections[current_section].append(numbered_match.group(1).strip())
        else:
            sections[current_section].append(line)

    output: dict[str, list[str] | str] = {}
    for key, values in sections.items():
        cleaned = [value for value in values if value]
        if key == "gate status":
            output[key] = cleaned[0] if cleaned else message_header_field(headers, "gate_status") or "unspecified"
        else:
            output[key] = cleaned
    return output


def relpath(path: Path, repo_root: Path) -> str:
    repo_root_abs = Path(os.path.abspath(repo_root))
    path_abs = Path(os.path.abspath(path))

    if os.path.commonpath((str(repo_root_abs), str(path_abs))) != str(repo_root_abs):
        raise ValueError(f"{path_abs!s} is not in the subpath of {repo_root_abs!s}")

    return path_abs.relative_to(repo_root_abs).as_posix()


def role_state_dir_names(runtime_role: str) -> tuple[str, ...]:
    preferred = ROLE_STATE_DIR_BY_RUNTIME.get(runtime_role, runtime_role)
    legacy = ROLE_STATE_LEGACY_DIRS.get(runtime_role, ())
    names = (preferred, *legacy)
    deduped: list[str] = []
    for name in names:
        if name not in deduped:
            deduped.append(name)
    return tuple(deduped)


def preferred_role_state_dir(repo_root: Path, runtime_role: str) -> Path:
    current_root = repo_root / "runs" / "current" / "role-state"
    for name in role_state_dir_names(runtime_role):
        candidate = current_root / name
        if candidate.exists():
            return candidate
    return current_root / role_state_dir_names(runtime_role)[0]


def all_role_state_dirs(repo_root: Path, runtime_role: str) -> list[Path]:
    current_root = repo_root / "runs" / "current" / "role-state"
    return [current_root / name for name in role_state_dir_names(runtime_role)]


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


def parse_simple_yaml(path: Path) -> dict[str, object]:
    payload: dict[str, object] = {}
    current_key: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        key_match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if key_match and not line.startswith("  "):
            current_key = key_match.group(1)
            value = key_match.group(2).strip()
            if value:
                payload[current_key] = value
                current_key = None
            else:
                payload[current_key] = []
            continue

        list_match = re.match(r"^\s*-\s+(.*)$", line)
        if list_match and current_key:
            current_value = payload.setdefault(current_key, [])
            if isinstance(current_value, list):
                current_value.append(list_match.group(1).strip())
            continue

    return payload


def phase_name_from_phase_doc(path_value: str) -> str | None:
    name = Path(path_value).name
    if not name.startswith("phase-") or not name.endswith(".md"):
        return None
    return name[:-3]


def canonical_artifacts_for_role_phases(
    repo_root: Path,
    runtime_role: str,
    phases: Iterable[str],
) -> list[str]:
    wanted_phases = {phase for phase in phases if phase}
    results: list[str] = []
    if not wanted_phases:
        return results

    for artifact_dir, template_path in iter_required_artifact_templates(repo_root):
        metadata = parse_metadata_block(template_path)
        owner = str(metadata.get("owner", "")).strip()
        phase = str(metadata.get("phase", "")).strip()
        if owner != runtime_role or phase not in wanted_phases:
            continue
        results.append(f"runs/current/artifacts/{artifact_dir}/{template_path.name}")

    return sorted(results)


def template_for_run_artifact(repo_root: Path, run_path: Path) -> Path | None:
    try:
        relative = relpath(run_path, repo_root)
    except ValueError:
        return None

    parts = relative.split("/")
    if len(parts) != 5 or parts[:3] != ["runs", "current", "artifacts"]:
        return None

    artifact_dir = parts[3]
    template_dir = RUN_ARTIFACT_TEMPLATE_DIRS.get(artifact_dir)
    if not template_dir:
        return None

    template_path = repo_root / template_dir / parts[4]
    if template_path.exists():
        return template_path
    return None


def owner_for_run_artifact(repo_root: Path, run_path: Path) -> str | None:
    template_path = template_for_run_artifact(repo_root, run_path)
    owner = ""
    if template_path is not None:
        owner = str(parse_metadata_block(template_path).get("owner", "")).strip()
    if not owner and run_path.exists():
        owner = str(parse_metadata_block(run_path).get("owner", "")).strip()
    return owner or None


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def owned_prefixes(runtime_role: str) -> tuple[str, ...]:
    try:
        return ROLE_OWNED_PREFIXES[runtime_role]
    except KeyError as exc:
        raise SystemExit(f"error: unknown runtime role: {runtime_role}") from exc


def path_matches_rule(relative_path: str, rule: str) -> bool:
    if any(token in rule for token in ("*", "?", "[")):
        return fnmatch(relative_path, rule)

    normalized = rule.rstrip("/")
    return relative_path == normalized or relative_path.startswith(f"{normalized}/")
