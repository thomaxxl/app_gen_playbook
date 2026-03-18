from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import subprocess
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .markdown import markdown_title, parse_frontmatter, parse_handoff_message, parse_markdown_document, parse_markdown_list
from .status_contract import (
    normalize_status_report_payload,
    readiness_ratio,
    should_include_artifact_file,
    summarize_package_status,
)


ROLE_ALIASES = {
    "deployment": "devops",
    "devops": "devops",
}

ROLE_DEFS = (
    ("product_manager", "Product Manager", True),
    ("architect", "Architect", True),
    ("frontend", "UX/UI + Frontend", True),
    ("backend", "Backend", True),
    ("devops", "DevOps", False),
    ("ceo", "CEO", False),
)

PHASE_DEFS = (
    ("phase-0-intake-and-framing", 0, "Intake and Framing", "product_manager", 10),
    ("phase-1-product-definition", 1, "Product Definition", "product_manager", 15),
    ("phase-2-architecture-contract", 2, "Architecture Contract", "architect", 15),
    ("phase-3-ux-and-interaction-design", 3, "UX and Interaction Design", "frontend", 10),
    ("phase-4-backend-design-and-rules-mapping", 4, "Backend Design and Rules Mapping", "backend", 10),
    ("phase-5-parallel-implementation", 5, "Parallel Implementation", "architect", 25),
    ("phase-6-integration-review", 6, "Integration Review", "architect", 10),
    ("phase-7-product-acceptance", 7, "Product Acceptance", "product_manager", 5),
)

PHASE_STATUS_MAP = {
    "not-started": "not_started",
    "in-progress": "in_progress",
    "blocked": "blocked",
    "complete": "completed",
}

RUN_MODE_MAP = {
    "new-full-run": "new_full_run",
    "iterative-change-run": "iterative_change_run",
    "app-only-hotfix": "app_only_hotfix",
    "playbook-maintenance": "playbook_maintenance",
}

RUN_STATUS_MAP = {
    "active": "active",
    "blocked": "blocked",
    "interrupted": "interrupted",
    "complete": "completed",
    "completed": "completed",
    "failed": "failed",
    "archived": "archived",
    "superseded": "superseded",
}

ARTIFACT_FAMILY_MAP = {
    "product": "product",
    "architecture": "architecture",
    "ux": "ux",
    "backend-design": "backend_design",
    "devops": "devops",
}

ARTIFACT_STATUS_MAP = {
    "stub": "stub",
    "draft": "draft",
    "ready-for-handoff": "ready_for_handoff",
    "approved": "approved",
    "blocked": "blocked",
    "superseded": "superseded",
}

CHECK_STATUS_MAP = {
    True: "pass",
    False: "fail",
}

ARTIFACT_TEMPLATE_DIRS = {
    "product": "product",
    "architecture": "architecture",
    "ux": "ux",
    "backend-design": "backend_design",
}

NAMESPACE = uuid.UUID("d3e545b7-9556-4d5d-9021-04663cb8f5c9")


def stable_uuid(*parts: str) -> str:
    return str(uuid.uuid5(NAMESPACE, "|".join(parts)))


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_role(value: str | None) -> str | None:
    if not value:
        return None
    stripped = value.strip()
    return ROLE_ALIASES.get(stripped, stripped)


def run_tool_json(playbook_root: Path, tool_relative_path: str, args: list[str]) -> dict[str, Any]:
    tool_path = playbook_root / tool_relative_path
    result = subprocess.run(
        ["python3", str(tool_path), *args],
        cwd=playbook_root,
        check=False,
        capture_output=True,
        text=True,
    )
    stdout = result.stdout.strip()
    if not stdout:
        raise RuntimeError(f"{tool_relative_path} produced no JSON output:\n{result.stderr}")
    return json.loads(stdout)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def infer_evidence_type(path: Path) -> str:
    name = path.name.lower()
    parts = {part.lower() for part in path.parts}
    if "orchestrator" in parts and path.suffix == ".log":
        return "commands"
    if "orchestrator" in parts:
        return "orchestrator"
    if "backend" in name and "test" in name:
        return "backend_tests"
    if "frontend" in name and "test" in name:
        return "frontend_tests"
    if "e2e" in name or "playwright" in name:
        return "e2e_tests"
    if "environment" in name:
        return "environment_notes"
    if "command" in name:
        return "commands"
    return "custom"


def parse_iso_ts(value: str | None) -> str | None:
    if not value:
        return None
    return str(value)


def has_active_run(playbook_root: Path) -> bool:
    return (playbook_root / "runs" / "current" / "orchestrator" / "run-status.json").exists()


def as_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def file_timestamp(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def package_summary_from_rows(packages: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    current_run_rows = [row for row in packages if row.get("root_path", "").startswith("runs/current/artifacts/")]
    return {
        row["family"]: {
            "overall_status": row["overall_status"],
            "total_count": row["total_count"],
            "stub_count": row["stub_count"],
            "draft_count": row["draft_count"],
            "ready_count": row["ready_count"],
            "approved_count": row["approved_count"],
            "blocked_count": row["blocked_count"],
            "superseded_count": row["superseded_count"],
            "updated_at": row["updated_at"],
            "readiness_ratio": row.get("readiness_ratio"),
        }
        for row in current_run_rows
    }


def file_excerpt(path: Path) -> str:
    if path.suffix in {".md", ".txt", ".log", ".jsonl", ".yaml", ".yml", ".json"}:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped[:280]
    return ""


def coerce_yaml_scalar(value: str) -> Any:
    stripped = value.strip().strip("'\"")
    if stripped == "":
        return ""
    if stripped == "[]":
        return []
    lowered = stripped.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    if re.fullmatch(r"-?\d+", stripped):
        return int(stripped)
    return stripped


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    data: dict[str, Any] = {}
    index = 0
    while index < len(lines):
        raw = lines[index]
        if not raw.strip() or raw.lstrip().startswith("#"):
            index += 1
            continue
        if raw.startswith(" "):
            index += 1
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if not match:
            index += 1
            continue
        key, value = match.group(1), match.group(2)
        if value == ">":
            folded: list[str] = []
            index += 1
            while index < len(lines) and (lines[index].startswith("  ") or not lines[index].strip()):
                folded.append(lines[index].strip())
                index += 1
            data[key] = " ".join(part for part in folded if part).strip()
            continue
        if value != "":
            data[key] = coerce_yaml_scalar(value)
            index += 1
            continue
        index += 1
        nested_lines: list[str] = []
        while index < len(lines) and (lines[index].startswith("  ") or not lines[index].strip()):
            nested_lines.append(lines[index])
            index += 1
        nested_content = [line for line in nested_lines if line.strip()]
        if not nested_content:
            data[key] = ""
            continue
        if all(line.lstrip().startswith("- ") for line in nested_content):
            data[key] = [line.lstrip()[2:].strip() for line in nested_content]
            continue
        nested_map: dict[str, Any] = {}
        for line in nested_content:
            nested_match = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(.*)$", line)
            if not nested_match:
                continue
            nested_map[nested_match.group(1)] = coerce_yaml_scalar(nested_match.group(2))
        data[key] = nested_map
    return data


def parse_filename_timestamp(name: str) -> str | None:
    match = re.match(r"^(?P<stamp>\d{8}-\d{6})-", name)
    if not match:
        return None
    return match.group("stamp")


def iso_from_filename_stamp(value: str | None) -> str | None:
    if not value:
        return None
    try:
        dt = datetime.strptime(value, "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def relative_to_playbook(playbook_root: Path, candidate: str | None) -> str | None:
    if not candidate:
        return None
    text = str(candidate).strip()
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(playbook_root.resolve()).as_posix()
        except ValueError:
            return None
    return path.as_posix()


def classify_run_file(path: Path) -> dict[str, Any]:
    rel = path.as_posix()
    parts = path.parts
    top_level_area = parts[2] if len(parts) > 2 else "root"
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    logical_group = "file"
    logical_subtype = path.suffix.lstrip(".") or "file"
    render_mode = "download"
    viewer_key = "raw_file"
    role_code = None
    phase_code = None
    artifact_family = None
    change_id = None
    queue_state = None

    if parts[:3] == ("runs", "current", "artifacts"):
        artifact_family = ARTIFACT_FAMILY_MAP.get(parts[3], parts[3].replace("-", "_")) if len(parts) > 3 else None
        logical_group = "artifact_doc"
        logical_subtype = artifact_family or "artifact"
        render_mode = "custom_view"
        viewer_key = "artifact_doc"
    elif parts[:3] == ("runs", "current", "role-state"):
        lane = parts[3] if len(parts) > 3 else None
        role_code = normalize_role(lane)
        queue_state = parts[4] if len(parts) > 4 and parts[4] in {"inbox", "inflight", "processed"} else None
        if path.name == "context.md":
            logical_group = "role_context"
            logical_subtype = lane or "role"
            render_mode = "markdown"
            viewer_key = "role_context"
        elif path.name == "AGENTS.md":
            logical_group = "role_agents"
            logical_subtype = lane or "role"
            render_mode = "markdown"
            viewer_key = "role_agents"
        elif path.suffix == ".md" and queue_state:
            logical_group = "handoff_message"
            logical_subtype = queue_state
            render_mode = "custom_view"
            viewer_key = "handoff_message"
    elif parts[:3] == ("runs", "current", "changes"):
        change_id = parts[3] if len(parts) > 3 else None
        if path.name == "request.md":
            logical_group = "change_request"
            logical_subtype = "request"
            render_mode = "custom_view"
            viewer_key = "change_request"
        elif path.name in {"classification.yaml", "impact-manifest.yaml", "promotion.yaml"}:
            logical_group = "change_manifest"
            logical_subtype = path.stem.replace("-", "_")
            render_mode = "yaml_tree"
            viewer_key = "change_manifest"
        elif "role-loads" in parts:
            logical_group = "change_role_load"
            logical_subtype = path.stem
            render_mode = "yaml_tree"
            viewer_key = "change_role_load"
            role_code = normalize_role(path.stem)
        elif "verification" in parts:
            logical_group = "change_verification"
            logical_subtype = "verification"
            render_mode = "markdown" if path.suffix == ".md" else "text"
            viewer_key = "change_verification"
        elif "candidate" in parts and "artifacts" in parts and path.suffix == ".md":
            logical_group = "artifact_doc"
            logical_subtype = "change_candidate"
            render_mode = "custom_view"
            viewer_key = "artifact_doc"
            artifact_index = parts.index("artifacts")
            if artifact_index + 1 < len(parts):
                artifact_family = ARTIFACT_FAMILY_MAP.get(parts[artifact_index + 1], parts[artifact_index + 1].replace("-", "_"))
    elif parts[:3] == ("runs", "current", "orchestrator"):
        if path.name == "run-status.json":
            logical_group = "run_status"
            logical_subtype = "run_status"
            render_mode = "custom_view"
            viewer_key = "run_status"
        elif path.name == "runtime-environment.json":
            logical_group = "runtime_environment"
            logical_subtype = "runtime_environment"
            render_mode = "json_tree"
            viewer_key = "runtime_environment"
        elif len(parts) > 4 and parts[3] == "workers":
            role_code = normalize_role(path.stem)
            logical_group = "worker_state"
            logical_subtype = path.stem
            render_mode = "custom_view"
            viewer_key = "worker_state"
        elif len(parts) > 4 and parts[3] == "sessions":
            role_code = normalize_role(path.stem)
            logical_group = "session_state"
            logical_subtype = path.stem
            render_mode = "custom_view"
            viewer_key = "session_state"
        elif path.suffix == ".md" and path.name.startswith("operator-action-required"):
            logical_group = "operator_action"
            logical_subtype = "resolved" if ".resolved." in path.name else "required"
            render_mode = "custom_view"
            viewer_key = "operator_action"
    elif parts[:3] == ("runs", "current", "evidence"):
        if "orchestrator" in parts:
            if "prompts" in parts and path.suffix == ".md":
                logical_group = "agent_prompt"
                logical_subtype = "prompt"
                render_mode = "markdown"
                viewer_key = "agent_turn_prompt"
            elif "final" in parts and path.suffix == ".md":
                logical_group = "agent_result"
                logical_subtype = "result"
                render_mode = "markdown"
                viewer_key = "agent_turn_result"
            elif "jsonl" in parts and path.suffix == ".jsonl":
                logical_group = "agent_events"
                logical_subtype = "events"
                render_mode = "text"
                viewer_key = "agent_turn_events"
            elif "logs" in parts and path.suffix == ".log":
                logical_group = "log_file"
                logical_subtype = "orchestrator_log"
                render_mode = "text"
                viewer_key = "timeline_log"
            elif path.name.endswith(".handoff-validation.json"):
                logical_group = "validation_report"
                logical_subtype = "handoff_validation"
                render_mode = "custom_view"
                viewer_key = "validation_report"
            elif path.name.endswith(".recovery-validation.json"):
                logical_group = "validation_report"
                logical_subtype = "recovery_validation"
                render_mode = "custom_view"
                viewer_key = "validation_report"
            elif path.name.endswith(".snapshot.json"):
                logical_group = "turn_snapshot"
                logical_subtype = "snapshot"
                render_mode = "json_tree"
                viewer_key = "turn_snapshot"
            elif path.name.endswith(".validation.md"):
                logical_group = "validation_report"
                logical_subtype = "validation_markdown"
                render_mode = "markdown"
                viewer_key = "validation_report"
        elif "quality" in parts:
            logical_group = "quality_report"
            logical_subtype = path.stem
            render_mode = "markdown" if path.suffix == ".md" else "text"
            viewer_key = "quality_report"
        elif "ui-previews" in parts and path.name == "manifest.md":
            logical_group = "quality_report"
            logical_subtype = "ui_preview_manifest"
            render_mode = "custom_view"
            viewer_key = "quality_report"
        elif path.suffix == ".json" and "baseline" in parts:
            logical_group = "baseline_snapshot"
            logical_subtype = "baseline_snapshot"
            render_mode = "custom_view"
            viewer_key = "baseline_snapshot"
            match = re.search(r"changes/(CR-\d{8}-\d{6})/", rel)
            change_id = match.group(1) if match else change_id
        elif path.suffix == ".md":
            logical_group = "quality_report"
            logical_subtype = path.stem
            render_mode = "markdown"
            viewer_key = "quality_report"
    elif parts[:2] == ("runs", "current"):
        logical_group = "run_root"
        logical_subtype = path.stem
        if path.suffix == ".md":
            render_mode = "markdown"
            viewer_key = "run_note"
        elif path.suffix == ".json":
            render_mode = "json_tree"
            viewer_key = "run_note"
        elif path.suffix == ".txt":
            render_mode = "text"
            viewer_key = "run_note"

    if path.suffix in {".yaml", ".yml"} and render_mode == "download":
        render_mode = "yaml_tree"
    elif path.suffix == ".json" and render_mode == "download":
        render_mode = "json_tree"
    elif path.suffix in {".md"} and render_mode == "download":
        render_mode = "markdown"
    elif path.suffix in {".log", ".jsonl", ".txt"} and render_mode == "download":
        render_mode = "text"

    return {
        "top_level_area": top_level_area,
        "logical_group": logical_group,
        "logical_subtype": logical_subtype,
        "render_mode": render_mode,
        "viewer_key": viewer_key,
        "role_code": role_code,
        "phase_code": phase_code,
        "artifact_family": artifact_family,
        "change_id": change_id,
        "queue_state": queue_state,
        "mime_type": mime_type,
    }


def collect_run_files(playbook_root: Path, run_db_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    current_root = playbook_root / "runs" / "current"
    now = utcnow()
    run_files: list[dict[str, Any]] = []
    markdown_documents: list[dict[str, Any]] = []
    markdown_sections: list[dict[str, Any]] = []
    if not current_root.exists():
        return run_files, markdown_documents, markdown_sections

    for file_path in sorted(path for path in current_root.rglob("*") if path.is_file()):
        rel_path = file_path.relative_to(playbook_root)
        rel = rel_path.as_posix()
        classification = classify_run_file(rel_path)
        file_id = stable_uuid(run_db_id, "run-file", rel)
        title = markdown_title(file_path) if file_path.suffix == ".md" else file_path.stem
        preview = file_excerpt(file_path)
        parser_status = "unsupported"
        parse_error = None

        row = {
            "id": file_id,
            "run_id": run_db_id,
            "relative_path": rel,
            "filename": file_path.name,
            "stem": file_path.stem,
            "extension": file_path.suffix.lstrip("."),
            "mime_type": classification["mime_type"],
            "file_size_bytes": file_path.stat().st_size,
            "modified_at": file_timestamp(file_path),
            "content_hash": sha256_file(file_path),
            "top_level_area": classification["top_level_area"],
            "logical_group": classification["logical_group"],
            "logical_subtype": classification["logical_subtype"],
            "render_mode": classification["render_mode"],
            "viewer_key": classification["viewer_key"],
            "role_code": classification["role_code"],
            "phase_code": classification["phase_code"],
            "artifact_family": classification["artifact_family"],
            "change_id": classification["change_id"],
            "queue_state": classification["queue_state"],
            "title": title,
            "preview_text": preview,
            "parser_status": parser_status,
            "parse_error": parse_error,
            "first_seen_at": now,
            "last_seen_at": now,
        }

        if file_path.suffix == ".md":
            try:
                parsed = parse_markdown_document(file_path)
                row["title"] = parsed["title"]
                row["preview_text"] = parsed["excerpt"]
                row["parser_status"] = "parsed"
                markdown_documents.append(
                    {
                        "file_id": file_id,
                        "title": parsed["title"],
                        "frontmatter_json": parsed["frontmatter_json"],
                        "excerpt": parsed["excerpt"],
                        "word_count": parsed["word_count"],
                        "line_count": parsed["line_count"],
                        "heading_index_json": parsed["heading_index_json"],
                    }
                )
                sections = parsed["sections"]
                if classification["logical_group"] == "handoff_message":
                    handoff = parse_handoff_message(file_path)
                    sections = [
                        {
                            "section_name": name,
                            "section_order": order,
                            "body_text": body,
                        }
                        for order, (name, body) in enumerate(handoff.get("_sections", {}).items())
                    ]
                for section in sections:
                    markdown_sections.append(
                        {
                            "id": stable_uuid(file_id, "section", str(section["section_order"]), str(section["section_name"])),
                            "file_id": file_id,
                            "section_name": section["section_name"],
                            "section_order": section["section_order"],
                            "body_text": section["body_text"],
                        }
                    )
            except Exception as exc:  # pragma: no cover - defensive
                row["parser_status"] = "parse_error"
                row["parse_error"] = str(exc)

        run_files.append(row)

    return run_files, markdown_documents, markdown_sections


def run_file_maps(run_files: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    rows_by_path = {row["relative_path"]: row for row in run_files}
    ids_by_path = {path: row["id"] for path, row in rows_by_path.items()}
    return rows_by_path, ids_by_path


def markdown_document_map(markdown_documents: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["file_id"]: row for row in markdown_documents}


def collect_artifact_specs(playbook_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    specs_root = playbook_root / "specs"
    for template_dir_name, family in ARTIFACT_TEMPLATE_DIRS.items():
        template_dir = specs_root / template_dir_name
        if not template_dir.exists():
            continue
        for path in sorted(template_dir.rglob("*.md")):
            if path.name == "README.md":
                continue
            metadata = parse_frontmatter(path)
            rel = path.relative_to(playbook_root).as_posix()
            rows.append(
                {
                    "id": stable_uuid("artifact-spec", rel),
                    "family": family,
                    "template_path": rel,
                    "filename": path.name,
                    "title": markdown_title(path),
                    "owner_role_code": normalize_role(str(metadata.get("owner", "")).strip()) or None,
                    "phase_code": str(metadata.get("phase", "")).strip() or None,
                    "required_by_default": True,
                    "optional_mode": None,
                    "metadata_json": metadata,
                }
            )
    return rows


def collect_artifacts(
    playbook_root: Path,
    run_db_id: str,
    run_files: list[dict[str, Any]],
    markdown_documents: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    docs_by_file_id = markdown_document_map(markdown_documents)
    rows_by_path, ids_by_path = run_file_maps(run_files)
    packages: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    dependencies: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    package_counts: dict[str, Counter[str]] = {}
    package_rows: dict[str, dict[str, Any]] = {}

    artifact_rows_by_path: dict[str, dict[str, Any]] = {}

    for file_row in run_files:
        rel = file_row["relative_path"]
        if file_row["logical_group"] != "artifact_doc":
            continue
        path = playbook_root / rel
        metadata = docs_by_file_id.get(file_row["id"], {}).get("frontmatter_json", {})
        status_raw = str(metadata.get("status", "unknown")).strip() or "unknown"
        status = ARTIFACT_STATUS_MAP.get(status_raw, "unknown")
        owner_role = normalize_role(str(metadata.get("owner", "")).strip()) or "architect"
        phase_code = str(metadata.get("phase", "")).strip() or "phase-0-intake-and-framing"
        unresolved = as_string_list(metadata.get("unresolved", []))
        depends_on = as_string_list(metadata.get("depends_on", []))
        scope = "change_candidate" if "/candidate/artifacts/" in rel else "current_run"
        family = file_row.get("artifact_family") or "artifact"
        package_id = stable_uuid(run_db_id, "artifact-package", scope, family) if scope == "current_run" else None

        artifact_row = {
            "id": stable_uuid(run_db_id, "artifact", rel),
            "run_id": run_db_id,
            "package_id": package_id,
            "file_id": file_row["id"],
            "path": rel,
            "artifact_scope": scope,
            "title": file_row["title"],
            "owner_role_code": owner_role,
            "phase_code": phase_code,
            "status": status,
            "raw_status": status_raw,
            "last_updated_by_role_code": normalize_role(str(metadata.get("last_updated_by", "")).strip()) or None,
            "unresolved": unresolved,
            "metadata_json": metadata,
            "content_hash": file_row["content_hash"],
            "updated_at": file_row["modified_at"],
        }
        artifact_rows_by_path[rel] = artifact_row
        artifacts.append(artifact_row)

        if scope == "current_run":
            package_counts.setdefault(family, Counter())[status] += 1
            package_rows.setdefault(
                family,
                {
                    "id": stable_uuid(run_db_id, "artifact-package", scope, family),
                    "run_id": run_db_id,
                    "family": family,
                    "root_path": f"runs/current/artifacts/{family.replace('_', '-')}",
                },
            )

        for dependency in depends_on:
            dependency_path = dependency
            if dependency_path.startswith("../"):
                dependency_path = str((Path(rel).parent / dependency_path).as_posix())
            resolved_path = dependency_path if dependency_path.startswith("runs/current/") else None
            dependencies.append(
                {
                    "artifact_id": artifact_row["id"],
                    "depends_on_artifact_id": None,
                    "depends_on_path": dependency_path,
                }
            )
            relationships.append(
                {
                    "id": stable_uuid(run_db_id, "file-rel", rel, "depends_on", dependency_path),
                    "run_id": run_db_id,
                    "source_file_id": file_row["id"],
                    "target_file_id": ids_by_path.get(resolved_path) if resolved_path else None,
                    "target_path": dependency_path,
                    "relation_type": "depends_on",
                    "context_json": {"artifact_path": rel},
                }
            )

    artifact_id_by_path = {row["path"]: row["id"] for row in artifacts}
    for dependency in dependencies:
        dependency["depends_on_artifact_id"] = artifact_id_by_path.get(dependency["depends_on_path"])

    for family, package_row in package_rows.items():
        counts = package_counts.get(family, Counter())
        package_row.update(
            {
                "overall_status": summarize_package_status(counts),
                "readiness_ratio": readiness_ratio(counts),
                "total_count": sum(counts.values()),
                "stub_count": counts["stub"],
                "draft_count": counts["draft"],
                "ready_count": counts["ready_for_handoff"],
                "approved_count": counts["approved"],
                "blocked_count": counts["blocked"],
                "superseded_count": counts["superseded"],
                "updated_at": utcnow(),
            }
        )
        packages.append(package_row)

    return packages, artifacts, dependencies, relationships


def collect_run_artifact_expectations(
    run_db_id: str,
    artifact_specs: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    run_files_by_path: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    artifact_by_path = {row["path"]: row for row in artifact_rows if row["artifact_scope"] == "current_run"}
    expectations: list[dict[str, Any]] = []
    for spec in artifact_specs:
        family = spec["family"].replace("_", "-")
        expected_path = f"runs/current/artifacts/{family}/{spec['filename']}"
        artifact_row = artifact_by_path.get(expected_path)
        file_row = run_files_by_path.get(expected_path)
        expectations.append(
            {
                "id": stable_uuid(run_db_id, "artifact-expectation", expected_path),
                "run_id": run_db_id,
                "artifact_spec_id": spec["id"],
                "expected_path": expected_path,
                "file_id": file_row["id"] if file_row else None,
                "exists": bool(file_row),
                "status": artifact_row["status"] if artifact_row else "missing",
                "unresolved_count": len(artifact_row["unresolved"]) if artifact_row else 0,
                "updated_at": artifact_row["updated_at"] if artifact_row else utcnow(),
            }
        )
    return expectations


def collect_handoffs(
    playbook_root: Path,
    run_db_id: str,
    run_files: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    resolution_index: dict[str, str] = {}
    rows_by_path, ids_by_path = run_file_maps(run_files)

    for file_row in run_files:
        if file_row["logical_group"] != "handoff_message":
            continue
        path = playbook_root / file_row["relative_path"]
        payload = parse_handoff_message(path)
        role_lane = file_row.get("role_code") or normalize_role(file_row["relative_path"].split("/")[3]) or ""
        gate_status_raw = str(payload.get("gate status", "unspecified")).strip().lower().replace(" ", "_")
        if gate_status_raw not in {"pass", "pass_with_assumptions", "blocked", "unspecified"}:
            gate_status_raw = "unspecified"
        row = {
            "id": stable_uuid(run_db_id, "handoff", file_row["relative_path"]),
            "run_id": run_db_id,
            "file_id": file_row["id"],
            "filename": file_row["filename"],
            "path": file_row["relative_path"],
            "role_lane": file_row["relative_path"].split("/")[3],
            "lane_role_code": role_lane,
            "state_dir": file_row.get("queue_state"),
            "message_key": stable_uuid(run_db_id, "handoff-key", file_row["relative_path"].split("/")[3], file_row["filename"]),
            "message_timestamp": iso_from_filename_stamp(parse_filename_timestamp(file_row["filename"])),
            "created_at": file_row["modified_at"],
            "from_role_code": normalize_role(str(payload.get("from", "")).strip()),
            "to_role_code": normalize_role(str(payload.get("to", "")).strip()) or role_lane,
            "topic": str(payload.get("topic", "")).strip() or None,
            "purpose": str(payload.get("purpose", "")).strip() or None,
            "gate_status": gate_status_raw,
            "message_state": {"inbox": "inbox", "inflight": "processing", "processed": "processed"}.get(file_row.get("queue_state"), "inbox"),
            "inbox_path": file_row["relative_path"],
            "processed_path": file_row["relative_path"] if file_row.get("queue_state") == "processed" else None,
            "supersedes_message_id": None,
            "supersedes_raw": str(payload.get("supersedes", "")).strip() or None,
            "supersedes_path": str(payload.get("supersedes", "")).strip() or None,
            "required_reads": as_string_list(payload.get("required reads", [])),
            "requested_outputs": as_string_list(payload.get("requested outputs", [])),
            "dependencies": as_string_list(payload.get("dependencies", [])),
            "blocking_issues": as_string_list(payload.get("blocking issues", [])),
            "implementation_evidence_json": as_string_list(payload.get("implementation evidence", [])),
            "raw_metadata_json": {key: value for key, value in payload.items() if not key.startswith("_")},
            "change_id": str(payload.get("change_id", "")).strip() or None,
            "validation_file_id": None,
            "snapshot_file_id": None,
            "result_file_id": None,
            "events_file_id": None,
            "notes": "\n".join(payload.get("notes", [])) if isinstance(payload.get("notes"), list) else None,
            "processed_at": file_row["modified_at"] if file_row.get("queue_state") == "processed" else None,
        }
        rows.append(row)
        resolution_index[file_row["relative_path"]] = row["id"]
        resolution_index[file_row["filename"]] = row["id"]
        resolution_index[f"{file_row['relative_path'].split('/')[3]}/{file_row['filename']}"] = row["id"]

        for index, required_read in enumerate(row["required_reads"]):
            relationships.append(
                {
                    "id": stable_uuid(run_db_id, "handoff-rel", file_row["relative_path"], "required_read", str(index), required_read),
                    "run_id": run_db_id,
                    "source_file_id": file_row["id"],
                    "target_file_id": ids_by_path.get(required_read),
                    "target_path": required_read,
                    "relation_type": "required_read",
                    "context_json": {"message_path": file_row["relative_path"]},
                }
            )
        for index, requested_output in enumerate(row["requested_outputs"]):
            relationships.append(
                {
                    "id": stable_uuid(run_db_id, "handoff-rel", file_row["relative_path"], "requested_output", str(index), requested_output),
                    "run_id": run_db_id,
                    "source_file_id": file_row["id"],
                    "target_file_id": ids_by_path.get(requested_output),
                    "target_path": requested_output,
                    "relation_type": "requested_output",
                    "context_json": {"message_path": file_row["relative_path"]},
                }
            )
        for index, dependency in enumerate(row["dependencies"]):
            relationships.append(
                {
                    "id": stable_uuid(run_db_id, "handoff-rel", file_row["relative_path"], "dependency", str(index), dependency),
                    "run_id": run_db_id,
                    "source_file_id": file_row["id"],
                    "target_file_id": ids_by_path.get(dependency),
                    "target_path": dependency,
                    "relation_type": "depends_on",
                    "context_json": {"message_path": file_row["relative_path"]},
                }
            )
        for index, issue in enumerate(row["blocking_issues"]):
            relationships.append(
                {
                    "id": stable_uuid(run_db_id, "handoff-rel", file_row["relative_path"], "blocking_issue", str(index), issue),
                    "run_id": run_db_id,
                    "source_file_id": file_row["id"],
                    "target_file_id": None,
                    "target_path": issue,
                    "relation_type": "blocking_issue_ref",
                    "context_json": {"message_path": file_row["relative_path"]},
                }
            )

    for row in rows:
        supersedes_raw = row.get("supersedes_raw")
        if not supersedes_raw:
            continue
        row["supersedes_message_id"] = resolution_index.get(str(supersedes_raw))
        relationships.append(
            {
                "id": stable_uuid(run_db_id, "handoff-rel", row["path"], "supersedes", str(supersedes_raw)),
                "run_id": run_db_id,
                "source_file_id": row["file_id"],
                "target_file_id": ids_by_path.get(str(supersedes_raw)),
                "target_path": str(supersedes_raw),
                "relation_type": "supersedes",
                "context_json": None,
            }
        )

    return rows, relationships


def build_turn_key(role: str, message_filename: str, started_at: str) -> str:
    started_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    started_stamp = started_dt.strftime("%Y%m%d-%H%M%S")
    return f"{role}-{message_filename.removesuffix('.md')}-{started_stamp}"


def build_evidence_indices(run_files: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    indices = {
        "prompt": {},
        "result": {},
        "events": {},
        "snapshot": {},
        "validation": {},
        "handoff_validation": {},
        "recovery_validation": {},
    }
    for row in run_files:
        rel = row["relative_path"]
        name = row["filename"]
        if row["logical_group"] == "agent_prompt" and name.endswith(".prompt.md"):
            indices["prompt"][name.removesuffix(".prompt.md")] = row["id"]
        elif row["logical_group"] == "agent_result" and name.endswith(".result.md"):
            indices["result"][name.removesuffix(".result.md")] = row["id"]
        elif row["logical_group"] == "agent_events" and name.endswith(".events.jsonl"):
            indices["events"][name.removesuffix(".events.jsonl")] = row["id"]
        elif row["logical_group"] == "turn_snapshot" and name.endswith(".snapshot.json"):
            indices["snapshot"][name.removesuffix(".snapshot.json")] = row["id"]
        elif row["logical_group"] == "validation_report" and name.endswith(".validation.md"):
            indices["validation"][name.removesuffix(".validation.md")] = row["id"]
        elif row["logical_group"] == "validation_report" and name.endswith(".handoff-validation.json"):
            indices["handoff_validation"][name.removesuffix(".handoff-validation.json")] = row["id"]
        elif row["logical_group"] == "validation_report" and name.endswith(".recovery-validation.json"):
            indices["recovery_validation"][name.removesuffix(".recovery-validation.json")] = row["id"]
    return indices


@dataclass
class OpenTurn:
    role: str
    message_filename: str
    started_at: str
    session_id: str | None
    model: str | None


def collect_worker_states(playbook_root: Path, run_db_id: str, run_files: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows_by_path, ids_by_path = run_file_maps(run_files)
    rows: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    workers_root = playbook_root / "runs" / "current" / "orchestrator" / "workers"
    if not workers_root.exists():
        return rows, relationships
    for path in sorted(workers_root.glob("*.json")):
        rel = path.relative_to(playbook_root).as_posix()
        payload = json.loads(path.read_text(encoding="utf-8"))
        prompt_rel = relative_to_playbook(playbook_root, payload.get("prompt_file"))
        row = {
            "id": stable_uuid(run_db_id, "worker-state", path.stem),
            "run_id": run_db_id,
            "role_code": normalize_role(str(payload.get("role", "")).strip()) or normalize_role(path.stem),
            "file_id": ids_by_path.get(rel),
            "change_id": str(payload.get("change_id", "")).strip() or None,
            "claimed_at": parse_iso_ts(payload.get("claimed_at")),
            "claimed_message": str(payload.get("claimed_message", "")).strip() or None,
            "last_heartbeat": parse_iso_ts(payload.get("last_heartbeat")),
            "prompt_file_id": ids_by_path.get(prompt_rel) if prompt_rel else None,
            "session_id": str(payload.get("session_id", "")).strip() or None,
            "status": str(payload.get("status", "")).strip() or None,
            "task_id": str(payload.get("task_id", "")).strip() or None,
            "updated_at": file_timestamp(path),
        }
        rows.append(row)
        if prompt_rel:
            relationships.append(
                {
                    "id": stable_uuid(run_db_id, "worker-rel", rel, "prompt", prompt_rel),
                    "run_id": run_db_id,
                    "source_file_id": row["file_id"],
                    "target_file_id": ids_by_path.get(prompt_rel),
                    "target_path": prompt_rel,
                    "relation_type": "worker_prompt_file",
                    "context_json": {"role": row["role_code"]},
                }
            )
    return rows, relationships


def collect_session_states(playbook_root: Path, run_db_id: str, run_files: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows_by_path, ids_by_path = run_file_maps(run_files)
    rows: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    sessions_root = playbook_root / "runs" / "current" / "orchestrator" / "sessions"
    if not sessions_root.exists():
        return rows, relationships
    for path in sorted(sessions_root.glob("*.json")):
        rel = path.relative_to(playbook_root).as_posix()
        payload = json.loads(path.read_text(encoding="utf-8"))
        source_jsonl_rel = relative_to_playbook(playbook_root, payload.get("source_jsonl"))
        row = {
            "id": stable_uuid(run_db_id, "session-state", path.stem),
            "run_id": run_db_id,
            "role_code": normalize_role(path.stem),
            "file_id": ids_by_path.get(rel),
            "cwd": str(payload.get("cwd", "")).strip() or None,
            "last_used_at": parse_iso_ts(payload.get("last_used_at")),
            "model": str(payload.get("model", "")).strip() or None,
            "resume_id": str(payload.get("resume_id", "")).strip() or None,
            "source_jsonl_file_id": ids_by_path.get(source_jsonl_rel) if source_jsonl_rel else None,
            "thread_id": str(payload.get("thread_id", "")).strip() or None,
            "updated_at": file_timestamp(path),
        }
        rows.append(row)
        if source_jsonl_rel:
            relationships.append(
                {
                    "id": stable_uuid(run_db_id, "session-rel", rel, "source-jsonl", source_jsonl_rel),
                    "run_id": run_db_id,
                    "source_file_id": row["file_id"],
                    "target_file_id": ids_by_path.get(source_jsonl_rel),
                    "target_path": source_jsonl_rel,
                    "relation_type": "session_source_jsonl",
                    "context_json": {"role": row["role_code"]},
                }
            )
    return rows, relationships


def collect_agent_turns(
    playbook_root: Path,
    run_db_id: str,
    run_files: list[dict[str, Any]],
    handoff_rows: list[dict[str, Any]],
    worker_rows: list[dict[str, Any]],
    session_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    log_path = playbook_root / "runs" / "current" / "evidence" / "orchestrator" / "logs" / "orchestrator.log"
    if not log_path.exists():
        return [], []

    rows_by_path, ids_by_path = run_file_maps(run_files)
    evidence_indices = build_evidence_indices(run_files)
    message_file_id_by_filename = {row["filename"]: row["file_id"] for row in handoff_rows}
    worker_by_role = {row["role_code"]: row for row in worker_rows if row.get("role_code")}
    session_by_role = {row["role_code"]: row for row in session_rows if row.get("role_code")}

    rows: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    open_turns: dict[tuple[str, str], list[OpenTurn]] = {}

    start_re = re.compile(
        r"^\[(?P<ts>[^]]+)\] agent-start role=(?P<role>\S+) model=(?P<model>\S+) message=(?P<message>\S+) session=(?P<session>\S+)$"
    )
    finish_re = re.compile(
        r"^\[(?P<ts>[^]]+)\] agent-finish role=(?P<role>\S+) message=(?P<message>\S+) summary=(?P<summary>.*)$"
    )

    for raw_line in log_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        start_match = start_re.match(line)
        if start_match:
            role = normalize_role(start_match.group("role")) or start_match.group("role")
            message = start_match.group("message")
            open_turns.setdefault((role, message), []).append(
                OpenTurn(
                    role=role,
                    message_filename=message,
                    started_at=start_match.group("ts"),
                    session_id=None if start_match.group("session") in {"new", ""} else start_match.group("session"),
                    model=start_match.group("model"),
                )
            )
            continue

        finish_match = finish_re.match(line)
        if not finish_match:
            continue
        role = normalize_role(finish_match.group("role")) or finish_match.group("role")
        message = finish_match.group("message")
        key = (role, message)
        starts = open_turns.get(key, [])
        started = starts.pop(0) if starts else OpenTurn(role, message, finish_match.group("ts"), None, None)
        if not starts and key in open_turns:
            open_turns.pop(key, None)

        evidence_key = build_turn_key(role, message, started.started_at)
        session_row = session_by_role.get(role)
        worker_row = worker_by_role.get(role)
        row = {
            "id": stable_uuid(run_db_id, "agent-turn", role, message, started.started_at),
            "run_id": run_db_id,
            "role_code": role,
            "message_filename": message,
            "message_file_id": message_file_id_by_filename.get(message),
            "prompt_file_id": evidence_indices["prompt"].get(evidence_key),
            "result_file_id": evidence_indices["result"].get(evidence_key),
            "events_file_id": evidence_indices["events"].get(evidence_key),
            "snapshot_file_id": evidence_indices["snapshot"].get(evidence_key),
            "validation_file_id": evidence_indices["validation"].get(evidence_key) or evidence_indices["handoff_validation"].get(evidence_key),
            "recovery_validation_file_id": evidence_indices["recovery_validation"].get(message.removesuffix(".md")),
            "worker_state_file_id": worker_row["file_id"] if worker_row else None,
            "session_state_file_id": session_row["file_id"] if session_row else None,
            "session_id": started.session_id,
            "model": started.model or (session_row.get("model") if session_row else None),
            "resume_id": session_row.get("resume_id") if session_row else None,
            "started_at": started.started_at,
            "finished_at": finish_match.group("ts"),
            "status": "complete",
            "summary": finish_match.group("summary").strip(),
            "jsonl_path": None,
            "result_path": None,
        }
        rows.append(row)

    for key, starts in open_turns.items():
        for started in starts:
            role = started.role
            message = started.message_filename
            evidence_key = build_turn_key(role, message, started.started_at)
            session_row = session_by_role.get(role)
            worker_row = worker_by_role.get(role)
            rows.append(
                {
                    "id": stable_uuid(run_db_id, "agent-turn", role, message, started.started_at),
                    "run_id": run_db_id,
                    "role_code": role,
                    "message_filename": message,
                    "message_file_id": message_file_id_by_filename.get(message),
                    "prompt_file_id": evidence_indices["prompt"].get(evidence_key),
                    "result_file_id": evidence_indices["result"].get(evidence_key),
                    "events_file_id": evidence_indices["events"].get(evidence_key),
                    "snapshot_file_id": evidence_indices["snapshot"].get(evidence_key),
                    "validation_file_id": evidence_indices["validation"].get(evidence_key) or evidence_indices["handoff_validation"].get(evidence_key),
                    "recovery_validation_file_id": evidence_indices["recovery_validation"].get(message.removesuffix(".md")),
                    "worker_state_file_id": worker_row["file_id"] if worker_row else None,
                    "session_state_file_id": session_row["file_id"] if session_row else None,
                    "session_id": started.session_id,
                    "model": started.model or (session_row.get("model") if session_row else None),
                    "resume_id": session_row.get("resume_id") if session_row else None,
                    "started_at": started.started_at,
                    "finished_at": None,
                    "status": "active",
                    "summary": None,
                    "jsonl_path": None,
                    "result_path": None,
                }
            )

    for row in rows:
        if row.get("message_file_id") and row.get("result_file_id"):
            relationships.append(
                {
                    "id": stable_uuid(run_db_id, "turn-rel", row["id"], "result", str(row["result_file_id"])),
                    "run_id": run_db_id,
                    "source_file_id": row["message_file_id"],
                    "target_file_id": row["result_file_id"],
                    "target_path": None,
                    "relation_type": "result_for",
                    "context_json": {"turn_id": row["id"]},
                }
            )
        for relation_type, key_name in (
            ("prompt_for", "prompt_file_id"),
            ("events_for", "events_file_id"),
            ("snapshot_for", "snapshot_file_id"),
            ("validation_for", "validation_file_id"),
        ):
            if row.get("message_file_id") and row.get(key_name):
                relationships.append(
                    {
                        "id": stable_uuid(run_db_id, "turn-rel", row["id"], relation_type, str(row[key_name])),
                        "run_id": run_db_id,
                        "source_file_id": row["message_file_id"],
                        "target_file_id": row[key_name],
                        "target_path": None,
                        "relation_type": relation_type,
                        "context_json": {"turn_id": row["id"]},
                    }
                )

    return rows, relationships


def link_handoffs_to_turns(handoff_rows: list[dict[str, Any]], agent_turn_rows: list[dict[str, Any]]) -> None:
    latest_turn_by_message: dict[str, dict[str, Any]] = {}
    for row in agent_turn_rows:
        latest_turn_by_message[row["message_filename"]] = row
    for handoff in handoff_rows:
        turn = latest_turn_by_message.get(handoff["filename"])
        if not turn:
            continue
        handoff["result_file_id"] = turn.get("result_file_id")
        handoff["events_file_id"] = turn.get("events_file_id")
        handoff["snapshot_file_id"] = turn.get("snapshot_file_id")
        handoff["validation_file_id"] = turn.get("validation_file_id")


def collect_change_requests(
    playbook_root: Path,
    run_db_id: str,
    run_files: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rows_by_path, ids_by_path = run_file_maps(run_files)
    requests: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    role_loads: list[dict[str, Any]] = []
    baseline_snapshots: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    changes_root = playbook_root / "runs" / "current" / "changes"
    if not changes_root.exists():
        return requests, items, role_loads, baseline_snapshots, relationships

    for change_dir in sorted(path for path in changes_root.iterdir() if path.is_dir()):
        change_id = change_dir.name
        request_rel = f"runs/current/changes/{change_id}/request.md"
        classification_rel = f"runs/current/changes/{change_id}/classification.yaml"
        impact_rel = f"runs/current/changes/{change_id}/impact-manifest.yaml"
        promotion_rel = f"runs/current/changes/{change_id}/promotion.yaml"
        classification = parse_simple_yaml(playbook_root / classification_rel) if (playbook_root / classification_rel).exists() else {}
        impact = parse_simple_yaml(playbook_root / impact_rel) if (playbook_root / impact_rel).exists() else {}
        promotion = parse_simple_yaml(playbook_root / promotion_rel) if (playbook_root / promotion_rel).exists() else {}
        accepted_at = str(promotion.get("accepted_at", "")).strip() or None
        current_state = "intake"
        if promotion:
            current_state = "completed" if accepted_at else "promoted"
        elif impact:
            current_state = "impacted"
        elif classification:
            current_state = "classified"
        request_row = {
            "id": stable_uuid(run_db_id, "change-request", change_id),
            "run_id": run_db_id,
            "change_id": change_id,
            "request_file_id": ids_by_path.get(request_rel),
            "classification_file_id": ids_by_path.get(classification_rel),
            "impact_manifest_file_id": ids_by_path.get(impact_rel),
            "promotion_file_id": ids_by_path.get(promotion_rel),
            "requested_mode": classification.get("requested_mode"),
            "reason": classification.get("reason"),
            "affected_domains_json": classification.get("affected_domains") or classification.get("affected_product_areas") or [],
            "needs_baseline_alignment": bool(classification.get("needs_baseline_alignment")),
            "baseline_id": classification.get("baseline_id") or impact.get("baseline_id") or promotion.get("new_baseline_id"),
            "created_at": rows_by_path.get(request_rel, {}).get("modified_at"),
            "accepted_at": accepted_at,
            "current_state": current_state,
        }
        requests.append(request_row)

        for rel in (request_rel, classification_rel, impact_rel, promotion_rel):
            if rel in ids_by_path:
                relationships.append(
                    {
                        "id": stable_uuid(run_db_id, "change-rel", change_id, "belongs_to", rel),
                        "run_id": run_db_id,
                        "source_file_id": ids_by_path[rel],
                        "target_file_id": ids_by_path.get(request_rel),
                        "target_path": request_rel,
                        "relation_type": "belongs_to_change",
                        "context_json": {"change_id": change_id},
                    }
                )

        combined_items: list[tuple[str, str, str | None]] = []
        for item_value in as_string_list(impact.get("affected_artifacts", [])):
            combined_items.append(("affected_artifact", item_value, impact_rel))
        for item_value in as_string_list(impact.get("affected_app_paths", [])):
            combined_items.append(("affected_app_path", item_value, impact_rel))
        for item_value in parse_markdown_list(change_dir / "reopened-gates.md") if (change_dir / "reopened-gates.md").exists() else []:
            combined_items.append(("reopened_gate", item_value, f"runs/current/changes/{change_id}/reopened-gates.md"))
        for item_value in as_string_list(promotion.get("promoted_artifacts", [])):
            combined_items.append(("promoted_artifact", item_value, promotion_rel))
        for item_value in as_string_list(promotion.get("promoted_app_paths", [])):
            combined_items.append(("promoted_app_path", item_value, promotion_rel))

        for item_type, item_value, source_rel in combined_items:
            item_row = {
                "id": stable_uuid(run_db_id, "change-item", change_id, item_type, item_value),
                "change_request_id": request_row["id"],
                "item_type": item_type,
                "item_value": item_value,
                "source_file_id": ids_by_path.get(source_rel) if source_rel else None,
                "related_file_id": ids_by_path.get(item_value),
            }
            items.append(item_row)
            relationships.append(
                {
                    "id": stable_uuid(run_db_id, "change-item-rel", change_id, item_type, item_value),
                    "run_id": run_db_id,
                    "source_file_id": item_row["source_file_id"],
                    "target_file_id": item_row["related_file_id"],
                    "target_path": item_value,
                    "relation_type": item_type,
                    "context_json": {"change_id": change_id},
                }
            )

        role_load_dir = change_dir / "role-loads"
        if role_load_dir.exists():
            for path in sorted(role_load_dir.glob("*.yaml")):
                rel = path.relative_to(playbook_root).as_posix()
                payload = parse_simple_yaml(path)
                role_loads.append(
                    {
                        "id": stable_uuid(run_db_id, "change-role-load", change_id, path.stem),
                        "change_request_id": request_row["id"],
                        "role_code": normalize_role(path.stem) or path.stem,
                        "file_id": ids_by_path.get(rel),
                        "baseline_id": payload.get("baseline_id"),
                        "read_artifacts_json": payload.get("read_artifacts") or [],
                        "candidate_artifacts_json": payload.get("candidate_artifacts") or [],
                        "read_app_paths_json": payload.get("read_app_paths") or [],
                        "write_app_paths_json": payload.get("write_app_paths") or [],
                        "required_feature_packs_json": payload.get("required_feature_packs") or [],
                        "verification_inputs_json": payload.get("verification_inputs") or [],
                    }
                )

        baseline_root = playbook_root / "runs" / "current" / "evidence" / "changes" / change_id / "baseline"
        if baseline_root.exists():
            for path in sorted(baseline_root.glob("*.json")):
                rel = path.relative_to(playbook_root).as_posix()
                payload = json.loads(path.read_text(encoding="utf-8"))
                entry_count = len(payload) if isinstance(payload, list) else len(payload.keys()) if isinstance(payload, dict) else 0
                app_path_count = len(payload.get("entries", [])) if isinstance(payload, dict) and isinstance(payload.get("entries"), list) else entry_count
                baseline_snapshots.append(
                    {
                        "id": stable_uuid(run_db_id, "baseline-snapshot", rel),
                        "run_id": run_db_id,
                        "change_request_id": request_row["id"],
                        "file_id": ids_by_path.get(rel),
                        "baseline_id": request_row["baseline_id"],
                        "captured_at": rows_by_path.get(rel, {}).get("modified_at"),
                        "entry_count": entry_count,
                        "app_path_count": app_path_count,
                        "summary_json": {"keys": list(payload.keys())[:20]} if isinstance(payload, dict) else {"type": type(payload).__name__},
                    }
                )

    return requests, items, role_loads, baseline_snapshots, relationships


def collect_orchestrator_events(playbook_root: Path, run_db_id: str, run_files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    log_rel = "runs/current/evidence/orchestrator/logs/orchestrator.log"
    rows_by_path, ids_by_path = run_file_maps(run_files)
    log_path = playbook_root / log_rel
    if not log_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    line_re = re.compile(r"^\[(?P<ts>[^]]+)\]\s+(?P<body>.*)$")
    agent_start_re = re.compile(r"^agent-start role=(?P<role>\S+) model=(?P<model>\S+) message=(?P<message>\S+) session=(?P<session>\S+)$")
    agent_finish_re = re.compile(r"^agent-finish role=(?P<role>\S+) message=(?P<message>\S+) summary=(?P<summary>.*)$")
    worker_start_re = re.compile(r"^worker-start role=(?P<role>\S+) pid=(?P<pid>\d+)$")
    recovery_re = re.compile(r"^recovery-queued note=(?P<note>.+)$")
    dashboard_watch_re = re.compile(r"^dashboard-watch-start pid=(?P<pid>\d+) log=(?P<log>.+)$")

    for index, raw_line in enumerate(log_path.read_text(encoding="utf-8").splitlines()):
        line = raw_line.strip()
        match = line_re.match(line)
        timestamp = match.group("ts") if match else None
        body = match.group("body") if match else line
        severity = "info"
        event_type = "log-line"
        role_code = None
        message_filename = None
        session_id = None
        worker_pid = None
        details: dict[str, Any] = {}

        if body.startswith("fatal:"):
            severity = "error"
            event_type = "fatal"
        elif body.startswith("blocked:"):
            severity = "error"
            event_type = "blocked"
        elif body == "playbook run complete":
            event_type = "playbook-complete"
        elif body.startswith("phase-5-ready"):
            event_type = "phase-5-ready"
        elif body.startswith("product-manager-skipped"):
            event_type = "product-manager-skipped"
            details["reason"] = body.split("reason=", 1)[1] if "reason=" in body else None
        elif body.startswith("execution-prereqs-ready"):
            event_type = "execution-prereqs-ready"
        elif body.startswith("execution-prereqs-blocked"):
            severity = "warning"
            event_type = "execution-prereqs-blocked"
        elif body.startswith("stall-ceo-intervention"):
            event_type = "stall-ceo-intervention"
            details["reason"] = body.split("reason=", 1)[1] if "reason=" in body else None
        elif agent_start_re.match(body):
            event_type = "agent-start"
            start = agent_start_re.match(body)
            assert start
            role_code = normalize_role(start.group("role"))
            message_filename = start.group("message")
            session_id = None if start.group("session") in {"new", ""} else start.group("session")
            details.update({"model": start.group("model")})
        elif agent_finish_re.match(body):
            event_type = "agent-finish"
            finish = agent_finish_re.match(body)
            assert finish
            role_code = normalize_role(finish.group("role"))
            message_filename = finish.group("message")
            details.update({"summary": finish.group("summary")})
        elif worker_start_re.match(body):
            event_type = "worker-start"
            worker = worker_start_re.match(body)
            assert worker
            role_code = normalize_role(worker.group("role"))
            worker_pid = int(worker.group("pid"))
        elif recovery_re.match(body):
            event_type = "recovery-queued"
            recovery = recovery_re.match(body)
            assert recovery
            details["note"] = recovery.group("note")
        elif dashboard_watch_re.match(body):
            event_type = "dashboard-watch-start"
            watch = dashboard_watch_re.match(body)
            assert watch
            worker_pid = int(watch.group("pid"))
            details["log"] = watch.group("log")
        elif body.startswith("dashboard-init-complete"):
            event_type = "dashboard-init-complete"
        elif body.startswith("dashboard-sync-complete"):
            event_type = "dashboard-sync-complete"
        elif body.startswith("orchestrator-escalated"):
            event_type = "orchestrator-escalated"
        rows.append(
            {
                "id": stable_uuid(run_db_id, "orchestrator-event", str(index), line),
                "run_id": run_db_id,
                "file_id": ids_by_path.get(log_rel),
                "timestamp": timestamp,
                "severity": severity,
                "event_type": event_type,
                "role_code": role_code,
                "message_filename": message_filename,
                "session_id": session_id,
                "worker_pid": worker_pid,
                "details_json": details,
                "summary_text": body,
                "raw_line": line,
            }
        )
    return rows


def collect_operator_actions(playbook_root: Path, run_db_id: str, run_files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_path, ids_by_path = run_file_maps(run_files)
    rows: list[dict[str, Any]] = []
    for file_row in run_files:
        if file_row["logical_group"] != "operator_action":
            continue
        path = playbook_root / file_row["relative_path"]
        ready_work = parse_markdown_list(path)
        resolved = ".resolved." in file_row["filename"]
        rows.append(
            {
                "id": stable_uuid(run_db_id, "operator-action", file_row["relative_path"]),
                "run_id": run_db_id,
                "file_id": file_row["id"],
                "state": "resolved" if resolved else "required",
                "opened_at": file_row["modified_at"],
                "resolved_at": file_row["modified_at"] if resolved else None,
                "title": file_row["title"],
                "summary": file_row["preview_text"],
                "ready_work_json": ready_work,
                "details_json": {"path": file_row["relative_path"]},
            }
        )
    return rows


def collect_evidence(run_db_id: str, run_files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for file_row in run_files:
        rel = file_row["relative_path"]
        if not rel.startswith("runs/current/evidence/"):
            continue
        rows.append(
            {
                "id": stable_uuid(run_db_id, "evidence", rel),
                "run_id": run_db_id,
                "file_id": file_row["id"],
                "evidence_type": infer_evidence_type(Path(rel)),
                "path": rel,
                "summary": file_row["title"],
                "role_code": file_row.get("role_code"),
                "phase_code": file_row.get("phase_code"),
                "change_request_id": file_row.get("change_id"),
                "state": "present",
                "render_mode": file_row.get("render_mode"),
                "viewer_key": file_row.get("viewer_key"),
                "captured_at": file_row["modified_at"],
            }
        )
    return rows


def evidence_id_by_path(evidence_items: list[dict[str, Any]]) -> dict[str, str]:
    return {row["path"]: row["id"] for row in evidence_items}


def first_evidence_id_by_path(evidence_items: list[dict[str, Any]], suffix: str) -> str | None:
    for row in evidence_items:
        if row["path"].endswith(suffix):
            return row["id"]
    return None


def artifact_by_suffix(artifacts: list[dict[str, Any]], suffix: str) -> dict[str, Any] | None:
    for row in artifacts:
        if row["path"].endswith(suffix):
            return row
    return None


def collect_verification_checks(
    run_db_id: str,
    status_payload: dict[str, Any],
    evidence_items: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    completion = status_payload.get("completion", {})
    evidence = status_payload.get("evidence", {})
    evidence_paths = evidence_id_by_path(evidence_items)
    integration_review = artifact_by_suffix(artifacts, "runs/current/artifacts/architecture/integration-review.md")
    acceptance_review = artifact_by_suffix(artifacts, "runs/current/artifacts/product/acceptance-review.md")

    check_specs = [
        ("completion_gate", "phase-7-product-acceptance", None, CHECK_STATUS_MAP.get(completion.get("complete")), None, json.dumps(completion), False, "resolve completion blockers"),
        ("phase5_ready", "phase-5-parallel-implementation", None, CHECK_STATUS_MAP.get(status_payload.get("phase5_ready")), None, json.dumps(status_payload.get("phase5_blockers", [])), False, "clear phase-5 blockers"),
        ("contract_samples_present", "phase-6-integration-review", "runs/current/evidence/contract-samples.md", "pass" if evidence.get("contract_samples_exists") else "fail", "runs/current/evidence/contract-samples.md", None, not evidence.get("contract_samples_exists"), "write contract samples evidence"),
        ("frontend_usability_present", "phase-6-integration-review", "runs/current/evidence/frontend-usability.md", "pass" if "runs/current/evidence/frontend-usability.md" in evidence_paths else "fail", "runs/current/evidence/frontend-usability.md", None, "runs/current/evidence/frontend-usability.md" not in evidence_paths, "write frontend usability evidence"),
        ("ui_previews_manifest_present", "phase-6-integration-review", "runs/current/evidence/ui-previews/manifest.md", "pass" if "runs/current/evidence/ui-previews/manifest.md" in evidence_paths else "fail", "runs/current/evidence/ui-previews/manifest.md", None, "runs/current/evidence/ui-previews/manifest.md" not in evidence_paths, "capture or document UI previews"),
        ("data_sourcing_audit_present", "phase-6-integration-review", "runs/current/evidence/quality/data-sourcing-audit.md", "pass" if "runs/current/evidence/quality/data-sourcing-audit.md" in evidence_paths else "fail", "runs/current/evidence/quality/data-sourcing-audit.md", None, "runs/current/evidence/quality/data-sourcing-audit.md" not in evidence_paths, "write data sourcing audit"),
        ("quality_summary_present", "phase-6-integration-review", "runs/current/evidence/quality/quality-summary.md", "pass" if "runs/current/evidence/quality/quality-summary.md" in evidence_paths else "fail", "runs/current/evidence/quality/quality-summary.md", None, "runs/current/evidence/quality/quality-summary.md" not in evidence_paths, "write quality summary"),
        ("integration_review_artifact", "phase-6-integration-review", None, "pass" if integration_review and integration_review["status"] in {"ready_for_handoff", "approved"} else "warning", None, integration_review["status"] if integration_review else "missing", not bool(integration_review), "update integration-review artifact"),
        ("acceptance_review_gate", "phase-7-product-acceptance", None, "pass" if acceptance_review and acceptance_review["status"] == "approved" else "fail", None, acceptance_review["status"] if acceptance_review else "missing", not bool(acceptance_review), "complete product acceptance"),
    ]

    rows: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    for name, phase_code, source_path, status, evidence_path, details, missing_evidence, next_step in check_specs:
        evidence_item_id = evidence_paths.get(evidence_path) if evidence_path else None
        row_id = stable_uuid(run_db_id, "verification", name)
        rows.append(
            {
                "id": row_id,
                "run_id": run_db_id,
                "phase_code": phase_code,
                "role_code": None,
                "owner_role_code": "architect" if phase_code == "phase-6-integration-review" else "product_manager" if phase_code == "phase-7-product-acceptance" else None,
                "source_file_id": evidence_item_id,
                "check_name": name,
                "status": status or "unknown",
                "evidence_item_id": evidence_item_id,
                "missing_evidence": missing_evidence,
                "next_step": next_step,
                "evidence_count": 1 if evidence_item_id else 0,
                "details": details,
                "started_at": None,
                "finished_at": utcnow(),
            }
        )
        if evidence_item_id:
            links.append(
                {
                    "id": stable_uuid(run_db_id, "verification-link", name, evidence_item_id),
                    "verification_check_id": row_id,
                    "evidence_item_id": evidence_item_id,
                }
            )
    return rows, links


def build_phase_rows(run_db_id: str, status_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for phase_code, details in status_payload.get("phases", {}).items():
        raw_state = str(details.get("state", "not-started"))
        rows.append(
            {
                "id": stable_uuid(run_db_id, "phase", phase_code),
                "run_id": run_db_id,
                "phase_code": phase_code,
                "status": PHASE_STATUS_MAP.get(raw_state, "in_progress"),
                "raw_status": raw_state,
                "started_at": None,
                "ended_at": None,
                "progress": float(details.get("score", 0.0)) * 100.0,
                "blocker_count": len(details.get("blocked", [])),
                "focus_summary": None,
                "raw_payload_json": details,
            }
        )
    return rows


def build_blockers(
    run_db_id: str,
    status_payload: dict[str, Any],
    artifacts: list[dict[str, Any]],
    handoffs: list[dict[str, Any]],
    run_files: list[dict[str, Any]],
    change_requests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    rows_by_path, ids_by_path = run_file_maps(run_files)
    change_id_map = {row["change_id"]: row["id"] for row in change_requests}

    def append_blocker(
        source_type: str,
        source_id: str,
        title: str,
        *,
        phase_code: str | None = None,
        role_code: str | None = None,
        severity: str = "medium",
        details: dict[str, Any] | None = None,
        source_file_id: str | None = None,
        change_request_id: str | None = None,
    ) -> None:
        key = (source_type, source_id, title)
        if key in seen:
            return
        seen.add(key)
        rows.append(
            {
                "id": stable_uuid(run_db_id, "blocker", source_type, source_id, title),
                "run_id": run_db_id,
                "phase_code": phase_code,
                "role_code": role_code,
                "source_type": source_type,
                "source_id": source_id or None,
                "source_file_id": source_file_id,
                "change_request_id": change_request_id,
                "severity": severity,
                "title": title,
                "details": json.dumps(details or {}, sort_keys=True) if details is not None else None,
                "raw_payload_json": details,
                "current_flag": True,
                "opened_at": utcnow(),
                "resolved_at": None,
                "state": "open",
            }
        )

    for blocker in status_payload.get("completion", {}).get("blockers", []):
        path = blocker.get("path", "")
        append_blocker(
            blocker.get("kind", "completion"),
            path,
            blocker.get("reason", "blocker"),
            phase_code=blocker.get("phase") or None,
            role_code=normalize_role(blocker.get("owner")) if blocker.get("owner") else None,
            severity="high" if "blocked" in blocker.get("reason", "") else "medium",
            details=blocker,
            source_file_id=ids_by_path.get(path),
        )

    for blocker in status_payload.get("phase5_blockers", []):
        append_blocker(
            blocker.get("kind", "phase5"),
            blocker.get("path", ""),
            blocker.get("reason", "phase-5 blocker"),
            phase_code=blocker.get("phase") or None,
            role_code=normalize_role(blocker.get("owner")) if blocker.get("owner") else None,
            severity="high",
            details=blocker,
            source_file_id=ids_by_path.get(blocker.get("path", "")),
        )

    for artifact in artifacts:
        if artifact["status"] == "blocked":
            append_blocker(
                "artifact-blocked",
                artifact["path"],
                "artifact status is blocked",
                phase_code=artifact["phase_code"],
                role_code=artifact["owner_role_code"],
                severity="high",
                details=artifact,
                source_file_id=artifact.get("file_id"),
            )
        for index, issue in enumerate(artifact.get("unresolved", [])):
            append_blocker(
                "artifact-unresolved",
                f"{artifact['path']}#{index}",
                str(issue),
                phase_code=artifact["phase_code"],
                role_code=artifact["owner_role_code"],
                severity="medium",
                details={"artifact_path": artifact["path"], "issue": issue},
                source_file_id=artifact.get("file_id"),
            )

    for handoff in handoffs:
        if handoff["gate_status"] != "blocked":
            continue
        append_blocker(
            "handoff-blocked",
            handoff["path"],
            handoff.get("topic") or handoff.get("purpose") or "blocked handoff",
            role_code=handoff.get("to_role_code"),
            severity="high",
            details=handoff,
            source_file_id=handoff.get("file_id"),
            change_request_id=change_id_map.get(handoff.get("change_id")),
        )

    for phase_code, details in status_payload.get("phases", {}).items():
        if details.get("state") != "blocked":
            continue
        append_blocker(
            "phase-blocked",
            phase_code,
            f"{phase_code} is blocked",
            phase_code=phase_code,
            severity="high",
            details=details,
        )

    liveness = status_payload.get("liveness", {})
    if liveness.get("stale"):
        append_blocker(
            "stale-run",
            liveness.get("latest_activity_at", "stale"),
            "orchestrator is stale with actionable work pending",
            severity="high",
            details=liveness,
        )

    return rows


def collect_run_status_snapshots(run_db_id: str, status_payload: dict[str, Any], completion_payload: dict[str, Any]) -> list[dict[str, Any]]:
    liveness = status_payload.get("liveness", {})
    return [
        {
            "id": stable_uuid(run_db_id, "run-status-snapshot", "status_report", utcnow()),
            "run_id": run_db_id,
            "captured_at": utcnow(),
            "source_tool": "status_report",
            "payload_json": status_payload,
            "current_phase_code": status_payload.get("current_phase_code"),
            "phase5_ready": status_payload.get("phase5_ready"),
            "completion_complete": bool(completion_payload.get("complete")),
            "latest_activity_at": liveness.get("latest_activity_at"),
            "latest_activity_source": liveness.get("latest_activity_source"),
            "blocker_count": len(completion_payload.get("blockers", [])),
        },
        {
            "id": stable_uuid(run_db_id, "run-status-snapshot", "check_completion", utcnow()),
            "run_id": run_db_id,
            "captured_at": utcnow(),
            "source_tool": "check_completion",
            "payload_json": completion_payload,
            "current_phase_code": status_payload.get("current_phase_code"),
            "phase5_ready": status_payload.get("phase5_ready"),
            "completion_complete": bool(completion_payload.get("complete")),
            "latest_activity_at": liveness.get("latest_activity_at"),
            "latest_activity_source": liveness.get("latest_activity_source"),
            "blocker_count": len(completion_payload.get("blockers", [])),
        },
    ]


def collect_dashboard_snapshot(
    run_db_id: str,
    status_payload: dict[str, Any],
    blockers: list[dict[str, Any]],
    package_summary: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    completion = status_payload.get("completion", {})
    evidence = status_payload.get("evidence", {})
    return {
        "id": str(uuid.uuid4()),
        "run_id": run_db_id,
        "captured_at": utcnow(),
        "current_phase_code": status_payload.get("current_phase_code"),
        "overall_progress": float(status_payload.get("overall_progress", 0.0)),
        "current_focus": evidence.get("latest_activity_source") or status_payload.get("liveness", {}).get("latest_activity_source"),
        "open_blockers": len(blockers),
        "inbox_depth_by_role": {role: details.get("inbox_count", 0) for role, details in status_payload.get("roles", {}).items()},
        "package_summary": package_summary,
        "verification_summary": {
            "phase5_ready": status_payload.get("phase5_ready"),
            "completion_complete": completion.get("complete"),
            "contract_samples_exists": evidence.get("contract_samples_exists"),
            "recovery_log_exists": evidence.get("recovery_log_exists"),
            "stale": status_payload.get("liveness", {}).get("stale", False),
        },
        "acceptance_summary": status_payload.get("phases", {}).get("phase-7-product-acceptance", {}),
    }


def collect_run_snapshot(playbook_root: Path, project_slug: str, project_name: str) -> dict[str, Any]:
    playbook_root = playbook_root.resolve()
    project_row = {
        "id": stable_uuid("project", project_slug),
        "slug": project_slug,
        "name": project_name,
        "repo_name": playbook_root.name,
        "default_branch": "main",
        "created_at": utcnow(),
    }
    roles = [{"code": code, "display_name": display_name, "is_core": is_core} for code, display_name, is_core in ROLE_DEFS]
    phases = [{"code": code, "ordinal": ordinal, "name": name, "lead_role_code": lead, "weight": weight} for code, ordinal, name, lead, weight in PHASE_DEFS]

    if not has_active_run(playbook_root):
        empty_status_payload = normalize_status_report_payload(
            {
                "generated_at": utcnow(),
                "current_phase": {"key": None, "label": ""},
                "current_phase_code": None,
                "overall_progress": 0.0,
                "roles": {},
                "artifact_areas": {},
                "artifacts": {},
                "completion": {"complete": False, "blockers": []},
                "phases": {},
                "phase5_ready": False,
                "phase5_blockers": [],
                "evidence": {},
                "liveness": {},
            }
        )
        return {
            "captured_at": utcnow(),
            "playbook_root": str(playbook_root),
            "active_run": False,
            "project": project_row,
            "run": None,
            "roles": roles,
            "phases_catalog": phases,
            "status_payload": empty_status_payload,
        }

    status_payload = run_tool_json(
        playbook_root,
        "tools/status_report.py",
        ["--repo-root", str(playbook_root), "--format", "json"],
    )
    completion_payload = run_tool_json(
        playbook_root,
        "tools/check_completion.py",
        ["--repo-root", str(playbook_root), "--json"],
    )
    status_payload["completion"] = completion_payload
    status_payload = normalize_status_report_payload(status_payload)

    run_status_path = playbook_root / "runs" / "current" / "orchestrator" / "run-status.json"
    run_status = json.loads(run_status_path.read_text(encoding="utf-8"))
    run_id_raw = str(run_status.get("run_id", "")).strip() or "RUN-UNKNOWN"
    run_db_id = stable_uuid(project_slug, run_id_raw)

    run_files, markdown_documents, markdown_sections = collect_run_files(playbook_root, run_db_id)
    run_files_by_path, ids_by_path = run_file_maps(run_files)
    artifact_specs = collect_artifact_specs(playbook_root)
    packages, artifacts, artifact_dependencies, artifact_relationships = collect_artifacts(playbook_root, run_db_id, run_files, markdown_documents)
    run_artifact_expectations = collect_run_artifact_expectations(run_db_id, artifact_specs, artifacts, run_files_by_path)
    handoffs, handoff_relationships = collect_handoffs(playbook_root, run_db_id, run_files)
    change_requests, change_request_items, change_role_loads, baseline_snapshots, change_relationships = collect_change_requests(playbook_root, run_db_id, run_files)
    worker_states, worker_relationships = collect_worker_states(playbook_root, run_db_id, run_files)
    session_states, session_relationships = collect_session_states(playbook_root, run_db_id, run_files)
    agent_turns, turn_relationships = collect_agent_turns(playbook_root, run_db_id, run_files, handoffs, worker_states, session_states)
    link_handoffs_to_turns(handoffs, agent_turns)
    evidence_items = collect_evidence(run_db_id, run_files)
    verification_checks, verification_check_evidence = collect_verification_checks(run_db_id, status_payload, evidence_items, artifacts)
    orchestrator_events = collect_orchestrator_events(playbook_root, run_db_id, run_files)
    operator_actions = collect_operator_actions(playbook_root, run_db_id, run_files)
    blockers = build_blockers(run_db_id, status_payload, artifacts, handoffs, run_files, change_requests)
    run_status_snapshots = collect_run_status_snapshots(run_db_id, status_payload, completion_payload)
    phase_rows = build_phase_rows(run_db_id, status_payload)
    file_relationships = (
        artifact_relationships
        + handoff_relationships
        + change_relationships
        + worker_relationships
        + session_relationships
        + turn_relationships
    )
    dashboard_snapshot = collect_dashboard_snapshot(run_db_id, status_payload, blockers, package_summary_from_rows(packages))

    run_number = int(re.sub(r"\D", "", run_id_raw) or "1")
    liveness = status_payload.get("liveness", {})
    run_row = {
        "id": run_db_id,
        "project_slug": project_slug,
        "project_name": project_name,
        "repo_name": playbook_root.name,
        "run_number": run_number,
        "mode": RUN_MODE_MAP.get(str(run_status.get("mode", "new-full-run")), "new_full_run"),
        "title": f"{project_name} {run_id_raw}",
        "source_brief_path": "runs/current/input.md",
        "source_root_path": "runs/current",
        "app_root_path": "app",
        "status": RUN_STATUS_MAP.get(str(run_status.get("status", "active")), "active"),
        "raw_status": str(run_status.get("status", "active")),
        "run_id_raw": run_id_raw,
        "change_id": str(run_status.get("change_id", "")).strip() or None,
        "current_phase_code": status_payload.get("current_phase_code"),
        "overall_progress": float(status_payload.get("overall_progress", 0.0)),
        "phase5_ready": bool(status_payload.get("phase5_ready")),
        "completion_complete": bool(completion_payload.get("complete")),
        "latest_activity_at": liveness.get("latest_activity_at"),
        "latest_activity_source": liveness.get("latest_activity_source"),
        "status_reason": completion_payload.get("blockers", [{}])[0].get("reason") if completion_payload.get("blockers") else None,
        "started_at": parse_iso_ts(run_status.get("started_at")),
        "ended_at": parse_iso_ts(run_status.get("ended_at")),
        "interrupted_at": parse_iso_ts(run_status.get("interrupted_at")),
        "resumed_at": parse_iso_ts(run_status.get("resumed_at")),
    }

    return {
        "captured_at": utcnow(),
        "playbook_root": str(playbook_root),
        "active_run": True,
        "project": project_row,
        "run": run_row,
        "roles": roles,
        "phases_catalog": phases,
        "run_files": run_files,
        "file_relationships": file_relationships,
        "markdown_documents": markdown_documents,
        "markdown_sections": markdown_sections,
        "artifact_specs": artifact_specs,
        "run_artifact_expectations": run_artifact_expectations,
        "run_phase_status": phase_rows,
        "artifact_packages": packages,
        "artifacts": artifacts,
        "artifact_dependencies": artifact_dependencies,
        "handoff_messages": handoffs,
        "change_requests": change_requests,
        "change_request_items": change_request_items,
        "change_request_role_loads": change_role_loads,
        "baseline_snapshots": baseline_snapshots,
        "blockers": blockers,
        "orchestrator_worker_states": worker_states,
        "orchestrator_session_states": session_states,
        "evidence_items": evidence_items,
        "verification_checks": verification_checks,
        "verification_check_evidence": verification_check_evidence,
        "agent_turns": agent_turns,
        "orchestrator_events": orchestrator_events,
        "operator_actions": operator_actions,
        "run_status_snapshots": run_status_snapshots,
        "dashboard_snapshot": dashboard_snapshot,
        "status_payload": status_payload,
    }
