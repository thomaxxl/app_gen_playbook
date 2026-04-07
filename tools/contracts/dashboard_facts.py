from __future__ import annotations

import json
import mimetypes
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from check_completion import collect_blockers
from execution_scope import active_scope_context
from orchestrator_common import (
    RUNTIME_TO_DISPLAY,
    hash_file,
    parse_message_headers,
    parse_message_sections,
    parse_metadata_block,
    relpath,
)
from routing_resolver import parse_yaml_subset
from status_report import (
    ARTIFACT_AREAS,
    CHANGE_PHASE_ORDER,
    PHASE_LABELS,
    ROLE_ORDER,
    artifact_area_summary,
    compute_current_phase,
    evidence_summary,
    load_json,
    phase_requirements,
    phase_summary,
    queue_summary,
    report_payload,
)


CHANGE_RUN_MODES = {"iterative-change-run", "app-only-hotfix"}
PHASE_OWNER = {
    "phase-0-intake-and-framing": "product_manager",
    "phase-1-product-definition": "product_manager",
    "phase-2-architecture-contract": "architect",
    "phase-3-ux-and-interaction-design": "frontend",
    "phase-4-backend-design-and-rules-mapping": "backend",
    "phase-5-parallel-implementation": "frontend",
    "phase-6-integration-review": "architect",
    "phase-7-product-acceptance": "product_manager",
    "phase-8-qa-pre-delivery-validation": "qa",
    "phase-I0-baseline-alignment": "product_manager",
    "phase-I1-change-intake-and-triage": "product_manager",
    "phase-I2-product-and-scope-delta": "product_manager",
    "phase-I3-architecture-and-contract-delta": "architect",
    "phase-I4-design-delta": "architect",
    "phase-I4-frontend-design-delta": "frontend",
    "phase-I4-backend-design-delta": "backend",
    "phase-I4-devops-delta": "deployment",
    "phase-I5-implementation-delta": "architect",
    "phase-I5-frontend-implementation-delta": "frontend",
    "phase-I5-backend-implementation-delta": "backend",
    "phase-I6-integration-and-regression-review": "architect",
    "phase-I7-change-acceptance": "product_manager",
    "complete": "ceo",
}
PACKAGE_LABELS = {
    "product": "Product",
    "architecture": "Architecture",
    "ux": "UX",
    "backend-design": "Backend Design",
    "devops": "DevOps",
}
MESSAGE_FILE_RE = re.compile(
    r"^(?P<stamp>\d{8}-\d{6})-from-(?P<from>.+?)-to-(?P<to>.+?)-(?P<topic>.+)\.md$"
)
REMARK_EVENT_TYPE_MAP = {
    "run complete": "run_completed",
    "run stalled": "run_stalled",
    "recovery notes queued": "recovery_queued",
    "invalid handoff rejected": "handoff_rejected",
    "role diff validation failed": "role_diff_validation_failed",
}


@dataclass(frozen=True)
class FileDomainRef:
    domain_id: str | None
    domain_type: str
    package_code: str | None = None
    phase_code: str | None = None
    role_code: str | None = None
    change_id: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_utc_from_ts(timestamp: float | None) -> str | None:
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_utc_from_filename_stamp(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "item"


def stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part).strip() for part in parts if str(part).strip())
    digest = hash(raw)
    return f"{prefix}-{digest[:12].upper()}"


def hash(value: str) -> str:
    import hashlib

    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def title_from_markdown(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
    except OSError:
        return path.stem
    return path.stem.replace("-", " ").replace("_", " ").strip() or path.stem


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def safe_stat_mtime(path: Path) -> float | None:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def safe_relative(repo_root: Path, path: Path | str) -> str:
    if isinstance(path, str):
        return path
    try:
        return relpath(path, repo_root)
    except ValueError:
        return path.as_posix()


def normalize_role(value: str | None) -> str | None:
    if not value:
        return None
    lowered = value.strip().lower().replace("-", "_")
    if lowered == "devops":
        return "deployment"
    return lowered


def message_state_for_path(path: Path) -> str:
    name = path.name
    if ".superseded." in name:
        return "superseded"
    if ".cancelled." in name:
        return "cancelled"
    if path.parent.name == "inbox":
        return "inbox"
    if path.parent.name == "inflight":
        return "inflight"
    if path.parent.name == "processed":
        return "processed"
    return path.parent.name


def parse_message_identity(path: Path, repo_root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    headers = parse_message_headers(text)
    sections = parse_message_sections(text, headers=headers)
    match = MESSAGE_FILE_RE.match(path.name)
    stamp = match.group("stamp") if match else ""
    filename_from = normalize_role(match.group("from")) if match else None
    filename_to = normalize_role(match.group("to")) if match else None
    filename_topic = match.group("topic") if match else path.stem
    from_role = normalize_role(headers.get("from")) or filename_from or "unknown"
    to_role = normalize_role(headers.get("to")) or filename_to or "unknown"
    change_id = headers.get("change_id", "").strip() or None
    topic = headers.get("topic", "").strip() or filename_topic
    purpose = headers.get("purpose", "").strip() or topic.replace("-", " ")
    supersedes = headers.get("supersedes", "").strip() or None
    created_at = iso_utc_from_filename_stamp(stamp) or iso_utc_from_ts(safe_stat_mtime(path))
    processed_at = iso_utc_from_ts(safe_stat_mtime(path)) if message_state_for_path(path) == "processed" else None
    gate_status = str(sections.get("gate status", "") or "unspecified").strip() or "unspecified"
    blocking_entries = sections.get("blocking issues", [])
    blocking_issue = blocking_entries[0] if isinstance(blocking_entries, list) and blocking_entries else None
    message_id = stable_id("MSG", safe_relative(repo_root, path))
    supersedes_message_id = stable_id("MSG", supersedes) if supersedes else None
    thread_basis = [change_id or "run", topic or path.stem, from_role or "unknown", to_role or "unknown"]
    return {
        "message_id": message_id,
        "thread_key": slug(":".join(thread_basis)),
        "filename": path.name,
        "relative_path": safe_relative(repo_root, path),
        "state": message_state_for_path(path),
        "from_role": from_role,
        "to_role": to_role,
        "topic": topic,
        "purpose": purpose,
        "gate_status": gate_status,
        "blocking_issue": blocking_issue,
        "required_reads": list(sections.get("required reads", [])),
        "requested_outputs": list(sections.get("requested outputs", [])),
        "dependencies": list(sections.get("dependencies", [])),
        "implementation_evidence": list(sections.get("implementation evidence", [])),
        "supersedes_message_id": supersedes_message_id,
        "change_id": change_id,
        "created_at": created_at,
        "processed_at": processed_at,
    }


def iter_message_paths(repo_root: Path) -> list[Path]:
    state_root = repo_root / "runs" / "current" / "role-state"
    paths: list[Path] = []
    if not state_root.exists():
        return paths
    for role_dir in sorted(path for path in state_root.iterdir() if path.is_dir()):
        for subdir_name in ("inbox", "inflight", "processed"):
            subdir = role_dir / subdir_name
            if not subdir.exists():
                continue
            paths.extend(sorted(path for path in subdir.glob("*.md") if path.is_file()))
    return paths


def build_handoffs(repo_root: Path) -> list[dict[str, Any]]:
    return [parse_message_identity(path, repo_root) for path in iter_message_paths(repo_root)]


def artifact_rows(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    artifact_roots = [
        repo_root / "runs" / "current" / "artifacts",
        repo_root / "runs" / "current" / "changes",
    ]
    for root in artifact_roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.md")):
            relative = safe_relative(repo_root, path)
            if "/role-state/" in relative or "/facts/" in relative or relative.endswith("README.md"):
                continue
            if relative.startswith("runs/current/changes/") and "/candidate/artifacts/" not in relative:
                continue
            metadata = parse_metadata_block(path)
            package_code = None
            change_id = None
            artifact_scope = "current_run"
            if relative.startswith("runs/current/artifacts/"):
                package_code = relative.split("/")[3]
            elif "/candidate/artifacts/" in relative:
                parts = relative.split("/")
                change_id = parts[2]
                package_code = parts[5]
                artifact_scope = "change_candidate"
            artifact_id = stable_id("ART", relative)
            rows.append(
                {
                    "artifact_id": artifact_id,
                    "path": relative,
                    "title": title_from_markdown(path),
                    "artifact_type": "markdown",
                    "artifact_scope": artifact_scope,
                    "package_code": package_code,
                    "phase_code": str(metadata.get("phase", "")).strip() or None,
                    "owner_role": normalize_role(str(metadata.get("owner", "")).strip()) or None,
                    "status": str(metadata.get("status", "")).strip() or "unknown",
                    "depends_on": list(metadata.get("depends_on", [])),
                    "unresolved": list(metadata.get("unresolved", [])),
                    "change_id": change_id,
                    "updated_at": iso_utc_from_ts(safe_stat_mtime(path)),
                }
            )
    return rows


def build_packages(repo_root: Path, artifact_rows_payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
    area_summary = artifact_area_summary(repo_root)
    unresolved_counts: dict[str, int] = {}
    for row in artifact_rows_payload:
        package_code = row.get("package_code")
        if not package_code:
            continue
        unresolved_counts[package_code] = unresolved_counts.get(package_code, 0) + (
            1 if row.get("unresolved") else 0
        )
    rows: list[dict[str, Any]] = []
    for package_code in ARTIFACT_AREAS:
        package = area_summary.get(package_code, {})
        counts = package.get("counts", {})
        rows.append(
            {
                "package_code": package_code,
                "label": PACKAGE_LABELS.get(package_code, package_code.replace("-", " ").title()),
                "readiness": str(package.get("overall_status", "empty")).replace("_", "-"),
                "artifact_count": int(package.get("file_count", 0)),
                "approved_count": int(counts.get("approved", 0)),
                "ready_for_handoff_count": int(counts.get("ready-for-handoff", 0) or counts.get("ready_for_handoff", 0)),
                "draft_count": int(counts.get("draft", 0)),
                "stub_count": int(counts.get("stub", 0)),
                "blocked_count": int(counts.get("blocked", 0)),
                "unresolved_count": int(unresolved_counts.get(package_code, 0)),
                "updated_at": package.get("latest_mtime") or None,
            }
        )
    return rows


def build_blockers(repo_root: Path, artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers = collect_blockers(repo_root)
    rows: list[dict[str, Any]] = []
    for blocker in blockers:
        path = str(blocker.get("path", "")).strip()
        phase_code = str(blocker.get("phase", "")).strip() or None
        owner_role = normalize_role(str(blocker.get("owner", "")).strip()) or None
        change_id = None
        if "/changes/" in path:
            match = re.search(r"runs/current/changes/([^/]+)/", path)
            if match:
                change_id = match.group(1)
        title = str(blocker.get("kind", "blocker")).replace("-", " ").replace("_", " ").title()
        summary = str(blocker.get("reason", "")).strip()
        severity = "high" if any(token in summary.lower() for token in ("blocked", "missing", "failed", "error")) else "medium"
        rows.append(
            {
                "blocker_id": stable_id("BLK", path or summary, phase_code or "", owner_role or ""),
                "title": title,
                "state": "open",
                "severity": severity,
                "source_type": "artifact" if path.endswith(".md") else "fact",
                "source_path": path or None,
                "owner_role": owner_role,
                "phase_code": phase_code,
                "change_id": change_id,
                "opened_at": None,
                "updated_at": utc_now(),
                "summary": summary,
                "next_action": str(blocker.get("alias_hint") or blocker.get("expected") or "").strip() or None,
            }
        )

    for artifact in artifacts:
        if artifact.get("status") != "blocked":
            continue
        source_path = str(artifact["path"])
        if any(existing["source_path"] == source_path for existing in rows):
            continue
        unresolved = artifact.get("unresolved") or []
        rows.append(
            {
                "blocker_id": stable_id("BLK", source_path),
                "title": f"{artifact['title']} blocked",
                "state": "open",
                "severity": "high",
                "source_type": "artifact",
                "source_path": source_path,
                "owner_role": artifact.get("owner_role"),
                "phase_code": artifact.get("phase_code"),
                "change_id": artifact.get("change_id"),
                "opened_at": artifact.get("updated_at"),
                "updated_at": artifact.get("updated_at"),
                "summary": unresolved[0] if unresolved else f"{artifact['title']} is blocked.",
                "next_action": None,
            }
        )
    return rows


def build_verification(repo_root: Path, blockers: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    missing_evidence_count = 0
    for blocker in blockers:
        path = str(blocker.get("source_path") or "")
        reason = str(blocker.get("summary") or "")
        is_evidence = "/evidence/" in path or "evidence" in reason.lower() or "preview" in reason.lower()
        status = "warning" if is_evidence else "blocked"
        if is_evidence:
            missing_evidence_count += 1
        checks.append(
            {
                "check_id": stable_id("CHK", blocker.get("blocker_id"), path, reason),
                "check_code": slug(str(blocker.get("title") or "check")),
                "label": str(blocker.get("title") or "Verification check"),
                "status": status,
                "role_code": blocker.get("owner_role"),
                "evidence_paths": [path] if path else [],
                "updated_at": blocker.get("updated_at"),
            }
        )

    verification_state = "complete"
    if checks:
        verification_state = "missing_evidence" if missing_evidence_count else "blocked"
    next_action = "Attach evidence for checks that still lack proof." if missing_evidence_count else (
        "Resolve remaining blocking checks before delivery." if checks else "No reviewer action required."
    )
    return {
        "verification_state": verification_state,
        "missing_evidence_count": missing_evidence_count,
        "checks": checks,
        "next_reviewer_action": next_action,
    }


def build_roles(repo_root: Path, blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queues = queue_summary(repo_root)
    workers_root = repo_root / "runs" / "current" / "orchestrator" / "workers"
    blocker_counts: dict[str, int] = {}
    for blocker in blockers:
        owner = blocker.get("owner_role")
        if owner:
            blocker_counts[owner] = blocker_counts.get(owner, 0) + 1
    rows: list[dict[str, Any]] = []
    for role in ROLE_ORDER:
        queue = queues.get(role, {})
        worker = load_json(workers_root / f"{role}.json") if workers_root.exists() else {}
        last_activity_candidates = [
            queue.get("context_exists") and safe_stat_mtime(repo_root / "runs" / "current" / "role-state" / ("devops" if role == "deployment" else role) / "context.md"),
            safe_stat_mtime(workers_root / f"{role}.json"),
        ]
        last_activity = max((value for value in last_activity_candidates if value), default=None)
        health = "idle"
        if queue.get("inflight_count", 0):
            health = "busy"
        elif queue.get("inbox_count", 0):
            health = "queued"
        elif blocker_counts.get(role, 0):
            health = "blocked"
        elif str(worker.get("status", "")).strip() == "interrupted":
            health = "interrupted"
        rows.append(
            {
                "role_code": role,
                "label": RUNTIME_TO_DISPLAY.get(role, role).replace("-", " ").title(),
                "health": health,
                "inbox_count": int(queue.get("inbox_count", 0)),
                "inflight_count": int(queue.get("inflight_count", 0)),
                "processed_count": int(queue.get("processed_count", 0)),
                "blocked_count": int(blocker_counts.get(role, 0)),
                "oldest_inbox_filename": queue.get("oldest_inbox") or None,
                "has_context": bool(queue.get("context_exists")),
                "last_activity_at": iso_utc_from_ts(last_activity),
            }
        )
    return rows


def _phase_timestamps(repo_root: Path, paths: list[str]) -> tuple[str | None, str | None]:
    timestamps = []
    for rel in paths:
        timestamp = safe_stat_mtime(repo_root / rel)
        if timestamp:
            timestamps.append(timestamp)
    if not timestamps:
        return None, None
    return iso_utc_from_ts(min(timestamps)), iso_utc_from_ts(max(timestamps))


def build_phases(repo_root: Path, run_status: dict[str, Any], roles_payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
    phases_map = phase_summary(repo_root)
    requirements = phase_requirements(repo_root)
    roles_lookup = {row["role_code"]: row for row in roles_payload}
    current_phase = compute_current_phase(
        repo_root,
        run_status,
        {role: {"inbox_count": rows.get("inbox_count", 0), "inflight_count": rows.get("inflight_count", 0)} for role, rows in {
            row["role_code"]: row for row in roles_payload
        }.items()},
        phases_map,
        str(run_status.get("status", "")).strip() == "complete",
    )
    scope_context = active_scope_context(repo_root)
    active_phases = list(scope_context.get("classification", {}).get("active_phases") or [])
    ordered_phase_codes = list(dict.fromkeys(
        list(phases_map.keys()) + [phase for phase in CHANGE_PHASE_ORDER if phase in active_phases]
    ))
    rows: list[dict[str, Any]] = []
    completion_state = str(run_status.get("status", "")).strip()
    current_index = ordered_phase_codes.index(current_phase) if current_phase in ordered_phase_codes else -1
    for index, phase_code in enumerate(ordered_phase_codes):
        phase = phases_map.get(phase_code)
        missing = list(phase.get("missing", [])) if phase else []
        blocked = list(phase.get("blocked", [])) if phase else []
        stub = list(phase.get("stub", [])) if phase else []
        score = float(phase.get("score", 0.0)) if phase else 0.0
        state = str(phase.get("state", "")) if phase else ""
        if not phase:
            if completion_state == "complete":
                state = "complete"
                score = 1.0
            elif current_index >= 0 and index < current_index:
                state = "complete"
                score = 1.0
            elif phase_code == current_phase:
                state = "blocked" if completion_state == "blocked" else "in-progress"
                score = 0.5
            else:
                state = "not-started"
                score = 0.0
        started_at, completed_at = _phase_timestamps(repo_root, requirements.get(phase_code, []))
        entry_gate_passed = not missing
        exit_gate_passed = state == "complete" and not blocked and not stub
        rows.append(
            {
                "phase_code": phase_code,
                "label": PHASE_LABELS.get(phase_code, phase_code),
                "owner_role": PHASE_OWNER.get(phase_code),
                "state": state,
                "score": round(score, 3),
                "missing_count": len(missing),
                "stub_count": len(stub),
                "blocked_count": len(blocked),
                "started_at": started_at,
                "completed_at": completed_at if state == "complete" else None,
                "is_current": phase_code == current_phase,
                "entry_gate_passed": entry_gate_passed,
                "exit_gate_passed": exit_gate_passed,
            }
        )
    return rows


def iter_run_files(repo_root: Path) -> list[Path]:
    run_root = repo_root / "runs" / "current"
    files: list[Path] = []
    for path in run_root.rglob("*"):
        if path.is_file() and "/facts/" not in path.as_posix():
            files.append(path)
    return sorted(files)


def render_mode_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".md":
        return "markdown"
    if suffix in {".json", ".jsonl", ".yaml", ".yml"}:
        return "custom"
    return "download"


def _domain_ref_for_file(
    repo_root: Path,
    relative: str,
    artifact_index: dict[str, dict[str, Any]],
    handoff_index: dict[str, dict[str, Any]],
) -> FileDomainRef:
    if relative in artifact_index:
        row = artifact_index[relative]
        return FileDomainRef(
            domain_id=row["artifact_id"],
            domain_type="artifact",
            package_code=row.get("package_code"),
            phase_code=row.get("phase_code"),
            role_code=row.get("owner_role"),
            change_id=row.get("change_id"),
        )
    if relative in handoff_index:
        row = handoff_index[relative]
        return FileDomainRef(
            domain_id=row["message_id"],
            domain_type="handoff",
            role_code=row.get("to_role"),
            change_id=row.get("change_id"),
        )
    if relative.startswith("runs/current/evidence/"):
        return FileDomainRef(domain_id=stable_id("EVID", relative), domain_type="evidence")
    if relative.startswith("runs/current/orchestrator/"):
        return FileDomainRef(domain_id=stable_id("ORCH", relative), domain_type="orchestrator")
    return FileDomainRef(domain_id=stable_id("FILE", relative), domain_type="file")


def build_files(
    repo_root: Path,
    artifacts: list[dict[str, Any]],
    handoffs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    artifact_index = {row["path"]: row for row in artifacts}
    handoff_index = {row["relative_path"]: row for row in handoffs}
    rows: list[dict[str, Any]] = []
    for path in iter_run_files(repo_root):
        relative = safe_relative(repo_root, path)
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        ref = _domain_ref_for_file(repo_root, relative, artifact_index, handoff_index)
        rows.append(
            {
                "file_id": stable_id("FILE", relative),
                "relative_path": relative,
                "filename": path.name,
                "file_type": path.suffix.lstrip(".").lower() or "unknown",
                "mime_type": mime_type,
                "size_bytes": path.stat().st_size,
                "sha256": hash_file(path),
                "domain_type": ref.domain_type,
                "domain_id": ref.domain_id,
                "package_code": ref.package_code,
                "phase_code": ref.phase_code,
                "role_code": ref.role_code,
                "change_id": ref.change_id,
                "render_mode": render_mode_for_path(path),
                "updated_at": iso_utc_from_ts(safe_stat_mtime(path)),
            }
        )
    return rows


def _sequence_for_changes(changes: list[dict[str, Any]]) -> dict[str, int]:
    ordered = sorted(
        changes,
        key=lambda row: (
            row.get("created_at") or "",
            row.get("change_id") or "",
        ),
    )
    return {row["change_id"]: index + 1 for index, row in enumerate(ordered)}


def build_change_requests(repo_root: Path, run_status: dict[str, Any]) -> list[dict[str, Any]]:
    changes_root = repo_root / "runs" / "current" / "changes"
    rows: list[dict[str, Any]] = []
    if not changes_root.exists():
        return rows
    current_change_id = str(run_status.get("change_id", "")).strip()
    for change_root in sorted(path for path in changes_root.iterdir() if path.is_dir()):
        change_id = change_root.name
        classification = parse_yaml_subset(change_root / "classification.yaml") if (change_root / "classification.yaml").exists() else {}
        impact = parse_yaml_subset(change_root / "impact-manifest.yaml") if (change_root / "impact-manifest.yaml").exists() else {}
        request_path = change_root / "request.md"
        title = title_from_markdown(request_path) if request_path.exists() else change_id
        created_at = iso_utc_from_ts(safe_stat_mtime(request_path if request_path.exists() else change_root))
        promotion = parse_yaml_subset(change_root / "promotion.yaml") if (change_root / "promotion.yaml").exists() else {}
        accepted_at = str(promotion.get("accepted_at", "")).strip()
        state = "completed" if accepted_at else "active"
        if current_change_id and change_id != current_change_id and not accepted_at:
            state = "pending"
        requested_mode = str(classification.get("requested_mode", "")).strip() or str(run_status.get("mode", "")).strip()
        impact_packages = []
        impact_roles = []
        for source in (classification, impact):
            for package in source.get("affected_domains", []) or []:
                if str(package) not in impact_packages:
                    impact_packages.append(str(package))
            for role in source.get("active_roles", []) or []:
                normalized = normalize_role(str(role))
                if normalized and normalized not in impact_roles:
                    impact_roles.append(normalized)
        rows.append(
            {
                "change_id": change_id,
                "title": title,
                "kind": requested_mode,
                "state": state,
                "sequence": 0,
                "requested_by": "operator",
                "created_at": created_at,
                "baseline_run_id": str(impact.get("baseline_id", "")).strip() or None,
                "summary": str(classification.get("reason", "")).strip() or None,
                "impact": {
                    "packages": impact_packages,
                    "roles": impact_roles,
                },
            }
        )
    sequences = _sequence_for_changes(rows)
    for row in rows:
        row["sequence"] = sequences.get(row["change_id"], 0)
    return rows


def build_run_lineage(run_status: dict[str, Any], change_requests: list[dict[str, Any]]) -> dict[str, Any]:
    current_change_id = str(run_status.get("change_id", "")).strip() or None
    current_change = next((row for row in change_requests if row["change_id"] == current_change_id), None)
    return {
        "run_id": run_status.get("run_id"),
        "mode": run_status.get("mode"),
        "current_change_id": current_change_id,
        "iteration_number": current_change.get("sequence") if current_change else None,
        "restored_from_run_id": run_status.get("restored_from_run_id") or None,
        "restored_from_change_id": run_status.get("restored_from_change_id") or None,
        "change_ids": [row["change_id"] for row in sorted(change_requests, key=lambda row: row["sequence"])],
    }


def build_recovery(repo_root: Path, run_status: dict[str, Any]) -> dict[str, Any]:
    runtime_env = load_json(repo_root / "runs" / "current" / "orchestrator" / "runtime-environment.json")
    recovery_state = "none"
    status = str(run_status.get("status", "")).strip()
    if status == "interrupted":
        recovery_state = "active"
    elif run_status.get("restored_from_run_id") or run_status.get("restored_from_change_id"):
        recovery_state = "restored"
    return {
        "recovery_state": recovery_state,
        "interrupted_at": runtime_env.get("interrupted_at"),
        "resumed_at": runtime_env.get("resumed_at"),
        "restored_from_run_id": run_status.get("restored_from_run_id") or None,
        "restored_from_change_id": run_status.get("restored_from_change_id") or None,
        "recovery_reason": runtime_env.get("recovery_reason") or None,
        "recovery_summary": runtime_env.get("recovery_summary") or None,
    }


def build_timeline(
    repo_root: Path,
    run_status: dict[str, Any],
    handoffs: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    run_id = str(run_status.get("run_id", "")).strip()
    for index, row in enumerate(read_jsonl(repo_root / "runs" / "current" / "remarks-events.jsonl"), start=1):
        title = str(row.get("title", "event")).strip()
        event_type = REMARK_EVENT_TYPE_MAP.get(title.lower(), "remark")
        timestamp = str(row.get("ts", "")).strip() or utc_now()
        events.append(
            {
                "event_id": stable_id("EVT", timestamp, title, index),
                "timestamp": timestamp,
                "event_type": event_type,
                "run_id": run_id,
                "change_id": None,
                "phase_code": None,
                "role_code": None,
                "title": title,
                "summary": str(row.get("body", "")).strip(),
                "source_path": "runs/current/remarks-events.jsonl",
                "related_ids": {
                    "artifact_id": None,
                    "blocker_id": None,
                    "message_id": None,
                },
            }
        )

    for handoff in handoffs:
        if handoff.get("created_at"):
            events.append(
                {
                    "event_id": stable_id("EVT", handoff["message_id"], "created"),
                    "timestamp": handoff["created_at"],
                    "event_type": "handoff_created",
                    "run_id": run_id,
                    "change_id": handoff.get("change_id"),
                    "phase_code": None,
                    "role_code": handoff.get("to_role"),
                    "title": f"Handoff created: {handoff.get('topic')}",
                    "summary": str(handoff.get("purpose") or handoff.get("topic") or "").strip(),
                    "source_path": handoff["relative_path"],
                    "related_ids": {
                        "artifact_id": None,
                        "blocker_id": None,
                        "message_id": handoff["message_id"],
                    },
                }
            )
        if handoff.get("processed_at"):
            events.append(
                {
                    "event_id": stable_id("EVT", handoff["message_id"], "processed"),
                    "timestamp": handoff["processed_at"],
                    "event_type": "handoff_processed",
                    "run_id": run_id,
                    "change_id": handoff.get("change_id"),
                    "phase_code": None,
                    "role_code": handoff.get("to_role"),
                    "title": f"Handoff processed: {handoff.get('topic')}",
                    "summary": str(handoff.get("purpose") or handoff.get("topic") or "").strip(),
                    "source_path": handoff["relative_path"],
                    "related_ids": {
                        "artifact_id": None,
                        "blocker_id": None,
                        "message_id": handoff["message_id"],
                    },
                }
            )

    for blocker in blockers:
        timestamp = blocker.get("updated_at") or utc_now()
        events.append(
            {
                "event_id": stable_id("EVT", blocker["blocker_id"], "open"),
                "timestamp": timestamp,
                "event_type": "blocker_opened",
                "run_id": run_id,
                "change_id": blocker.get("change_id"),
                "phase_code": blocker.get("phase_code"),
                "role_code": blocker.get("owner_role"),
                "title": blocker.get("title"),
                "summary": blocker.get("summary"),
                "source_path": blocker.get("source_path"),
                "related_ids": {
                    "artifact_id": None,
                    "blocker_id": blocker["blocker_id"],
                    "message_id": None,
                },
            }
        )

    return sorted(events, key=lambda row: (row.get("timestamp") or "", row["event_id"]))


def build_run_summary(
    repo_root: Path,
    status_payload: dict[str, Any],
    blockers: list[dict[str, Any]],
    verification: dict[str, Any],
    change_requests: list[dict[str, Any]],
    recovery: dict[str, Any],
) -> dict[str, Any]:
    run_status = status_payload.get("run_status", {})
    current_change_id = str(run_status.get("change_id", "")).strip() or None
    current_change = next((row for row in change_requests if row["change_id"] == current_change_id), None)
    role_rows = status_payload.get("roles", {})
    open_queue_work = sum(
        int(info.get("inbox_count", 0)) + int(info.get("inflight_count", 0))
        for info in role_rows.values()
    )
    return {
        "run_id": run_status.get("run_id"),
        "project_slug": slug(repo_root.name.replace("_", "-")),
        "run_status": run_status.get("status"),
        "mode": run_status.get("mode"),
        "current_phase_code": status_payload.get("current_phase_code"),
        "current_phase_label": status_payload.get("current_phase", {}).get("label"),
        "phase5_ready": bool(status_payload.get("phase5_ready")),
        "completion_complete": bool(status_payload.get("completion", {}).get("complete")),
        "latest_activity_at": status_payload.get("evidence", {}).get("latest_activity") or run_status.get("updated_at"),
        "latest_activity_source": status_payload.get("evidence", {}).get("latest_activity_source") or "run-status.json",
        "open_blocker_count": len(blockers),
        "open_queue_work": open_queue_work,
        "verification_state": verification.get("verification_state"),
        "current_change_id": current_change_id,
        "iteration_number": current_change.get("sequence") if current_change else None,
        "restored_from_run_id": recovery.get("restored_from_run_id"),
        "restored_from_change_id": recovery.get("restored_from_change_id"),
    }


def build_dashboard_facts(repo_root: Path) -> dict[str, Any]:
    status_payload = report_payload(repo_root)
    run_status = status_payload.get("run_status", {})
    artifacts = artifact_rows(repo_root)
    handoffs = build_handoffs(repo_root)
    blockers = build_blockers(repo_root, artifacts)
    verification = build_verification(repo_root, blockers)
    change_requests = build_change_requests(repo_root, run_status)
    recovery = build_recovery(repo_root, run_status)
    packages = build_packages(repo_root, artifacts)
    phases = build_phases(repo_root, run_status, build_roles(repo_root, blockers))
    files = build_files(repo_root, artifacts, handoffs)
    timeline = build_timeline(repo_root, run_status, handoffs, blockers)
    run_lineage = build_run_lineage(run_status, change_requests)
    roles = build_roles(repo_root, blockers)
    run_summary = build_run_summary(
        repo_root,
        status_payload,
        blockers,
        verification,
        change_requests,
        recovery,
    )
    return {
        "run_summary": run_summary,
        "phases": phases,
        "roles": roles,
        "blockers": blockers,
        "handoffs": handoffs,
        "timeline": timeline,
        "packages": packages,
        "artifacts": artifacts,
        "verification": verification,
        "files": files,
        "change_requests": change_requests,
        "run_lineage": run_lineage,
        "recovery": recovery,
    }
