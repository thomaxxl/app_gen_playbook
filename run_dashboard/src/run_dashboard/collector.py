from __future__ import annotations

import hashlib
import json
import re
import subprocess
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .markdown import markdown_title, parse_frontmatter, parse_handoff_message
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
    return value


def has_active_run(playbook_root: Path) -> bool:
    return (playbook_root / "runs" / "current" / "orchestrator" / "run-status.json").exists()


def as_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def package_summary_from_rows(packages: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
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
            "readiness_ratio": readiness_ratio(
                {
                    "stub": row["stub_count"],
                    "draft": row["draft_count"],
                    "ready_for_handoff": row["ready_count"],
                    "approved": row["approved_count"],
                    "blocked": row["blocked_count"],
                    "superseded": row["superseded_count"],
                }
            ),
        }
        for row in packages
    }


def collect_artifacts(playbook_root: Path, run_db_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    artifacts_root = playbook_root / "runs" / "current" / "artifacts"
    packages: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    dependencies: list[dict[str, Any]] = []

    for family_dir in sorted(path for path in artifacts_root.iterdir() if path.is_dir()):
        family_raw = family_dir.name
        family = ARTIFACT_FAMILY_MAP.get(family_raw, family_raw.replace("-", "_"))
        package_id = stable_uuid(run_db_id, "artifact-package", family_raw)
        counts: Counter[str] = Counter()
        area_artifacts: list[dict[str, Any]] = []

        for file_path in sorted(candidate for candidate in family_dir.rglob("*.md") if should_include_artifact_file(candidate.relative_to(family_dir))):
            if file_path.name == "README.md":
                continue
            metadata = parse_frontmatter(file_path)
            status_raw = str(metadata.get("status", "unknown")).strip() or "unknown"
            status = ARTIFACT_STATUS_MAP.get(status_raw, "unknown")
            owner_role = normalize_role(str(metadata.get("owner", "")).strip()) or "architect"
            phase_code = str(metadata.get("phase", "")).strip() or "phase-0-intake-and-framing"
            artifact_path = file_path.relative_to(playbook_root).as_posix()
            artifact_id = stable_uuid(run_db_id, "artifact", artifact_path)
            unresolved = as_string_list(metadata.get("unresolved", []))
            depends_on = as_string_list(metadata.get("depends_on", []))

            artifact_row = {
                "id": artifact_id,
                "run_id": run_db_id,
                "package_id": package_id,
                "path": artifact_path,
                "title": markdown_title(file_path),
                "owner_role_code": owner_role,
                "phase_code": phase_code,
                "status": status,
                "raw_status": status_raw,
                "last_updated_by_role_code": normalize_role(str(metadata.get("last_updated_by", "")).strip()) or None,
                "unresolved": unresolved,
                "content_hash": sha256_file(file_path),
                "updated_at": datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            counts[status] += 1
            area_artifacts.append(artifact_row)

            for dependency in depends_on:
                dependencies.append(
                    {
                        "artifact_id": artifact_id,
                        "depends_on_artifact_id": None,
                        "depends_on_path": dependency,
                    }
                )

        packages.append(
            {
                "id": package_id,
                "run_id": run_db_id,
                "family": family,
                "root_path": family_dir.relative_to(playbook_root).as_posix(),
                "overall_status": summarize_package_status(counts),
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
        artifacts.extend(area_artifacts)

    return packages, artifacts, dependencies


def collect_handoffs(playbook_root: Path, run_db_id: str) -> list[dict[str, Any]]:
    role_state_root = playbook_root / "runs" / "current" / "role-state"
    rows: list[dict[str, Any]] = []
    resolution_index: dict[str, str] = {}
    for role_dir in sorted(path for path in role_state_root.iterdir() if path.is_dir()):
        role_code = normalize_role(role_dir.name) or role_dir.name
        for state_dir_name, message_state in (("inbox", "inbox"), ("inflight", "processing"), ("processed", "processed")):
            message_dir = role_dir / state_dir_name
            if not message_dir.exists():
                continue
            for path in sorted(message_dir.glob("*.md")):
                if path.name == "README.md":
                    continue
                payload = parse_handoff_message(path)
                rel_path = path.relative_to(playbook_root).as_posix()
                created_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                gate_status_raw = str(payload.get("gate status", "unspecified")).strip().lower().replace(" ", "_")
                if gate_status_raw not in {"pass", "pass_with_assumptions", "blocked", "unspecified"}:
                    gate_status_raw = "unspecified"
                message_id = stable_uuid(run_db_id, "handoff", rel_path)
                supersedes_raw = str(payload.get("supersedes", "")).strip() or None
                row = {
                    "id": message_id,
                    "run_id": run_db_id,
                    "filename": path.name,
                    "path": rel_path,
                    "role_lane": role_dir.name,
                    "state_dir": state_dir_name,
                    "message_key": stable_uuid(run_db_id, "handoff-key", role_dir.name, path.name),
                    "created_at": created_at,
                    "from_role_code": normalize_role(str(payload.get("from", "")).strip()),
                    "to_role_code": normalize_role(str(payload.get("to", "")).strip()) or role_code,
                    "topic": str(payload.get("topic", "")).strip() or None,
                    "purpose": str(payload.get("purpose", "")).strip() or None,
                    "gate_status": gate_status_raw,
                    "message_state": message_state,
                    "inbox_path": rel_path,
                    "processed_path": rel_path if message_state == "processed" else None,
                    "supersedes_message_id": None,
                    "supersedes_raw": supersedes_raw,
                    "required_reads": as_string_list(payload.get("required reads", [])),
                    "requested_outputs": as_string_list(payload.get("requested outputs", [])),
                    "dependencies": as_string_list(payload.get("dependencies", [])),
                    "blocking_issues": as_string_list(payload.get("blocking issues", [])),
                    "notes": "\n".join(payload.get("notes", [])) if isinstance(payload.get("notes"), list) else None,
                    "processed_at": created_at if message_state == "processed" else None,
                }
                rows.append(row)
                resolution_index[rel_path] = message_id
                resolution_index[path.name] = message_id
                resolution_index[f"{role_dir.name}/{path.name}"] = message_id

    for row in rows:
        supersedes_raw = row.get("supersedes_raw")
        if not supersedes_raw:
            continue
        row["supersedes_message_id"] = resolution_index.get(str(supersedes_raw))
    return rows


@dataclass
class OpenTurn:
    role: str
    message_filename: str
    started_at: str
    session_id: str | None


def build_turn_evidence_index(playbook_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    orchestrator_root = playbook_root / "runs" / "current" / "evidence" / "orchestrator"
    jsonl_root = orchestrator_root / "jsonl"
    final_root = orchestrator_root / "final"
    return (
        {
            path.name.removesuffix(".events.jsonl"): path.relative_to(playbook_root).as_posix()
            for path in jsonl_root.glob("*.events.jsonl")
        }
        if jsonl_root.exists()
        else {},
        {
            path.name.removesuffix(".result.md"): path.relative_to(playbook_root).as_posix()
            for path in final_root.glob("*.result.md")
        }
        if final_root.exists()
        else {},
    )


def turn_evidence_key(role: str, message_filename: str, started_at: str) -> str:
    started_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    started_stamp = started_dt.strftime("%Y%m%d-%H%M%S")
    return f"{role}-{message_filename.removesuffix('.md')}-{started_stamp}"


def collect_agent_turns(playbook_root: Path, run_db_id: str) -> list[dict[str, Any]]:
    log_path = playbook_root / "runs" / "current" / "evidence" / "orchestrator" / "logs" / "orchestrator.log"
    if not log_path.exists():
        return []

    rows: list[dict[str, Any]] = []
    open_turns: dict[tuple[str, str], list[OpenTurn]] = {}
    jsonl_index, result_index = build_turn_evidence_index(playbook_root)

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
                )
            )
            continue

        finish_match = finish_re.match(line)
        if finish_match:
            role = normalize_role(finish_match.group("role")) or finish_match.group("role")
            message = finish_match.group("message")
            key = (role, message)
            starts = open_turns.get(key, [])
            started = starts.pop(0) if starts else OpenTurn(role, message, finish_match.group("ts"), None)
            if not starts and key in open_turns:
                open_turns.pop(key, None)
            rows.append(
                {
                    "id": stable_uuid(run_db_id, "agent-turn", role, message, started.started_at),
                    "run_id": run_db_id,
                    "role_code": role,
                    "message_filename": message,
                    "session_id": started.session_id,
                    "started_at": started.started_at,
                    "finished_at": finish_match.group("ts"),
                    "status": "complete",
                    "summary": finish_match.group("summary").strip(),
                    "jsonl_path": jsonl_index.get(turn_evidence_key(role, message, started.started_at)),
                    "result_path": result_index.get(turn_evidence_key(role, message, started.started_at)),
                }
            )

    for key, starts in open_turns.items():
        for started in starts:
            rows.append(
                {
                    "id": stable_uuid(run_db_id, "agent-turn", started.role, started.message_filename, started.started_at),
                    "run_id": run_db_id,
                    "role_code": started.role,
                    "message_filename": started.message_filename,
                    "session_id": started.session_id,
                    "started_at": started.started_at,
                    "finished_at": None,
                    "status": "active",
                    "summary": None,
                    "jsonl_path": jsonl_index.get(turn_evidence_key(started.role, started.message_filename, started.started_at)),
                    "result_path": result_index.get(turn_evidence_key(started.role, started.message_filename, started.started_at)),
                }
            )

    return rows


def collect_evidence(playbook_root: Path, run_db_id: str) -> list[dict[str, Any]]:
    evidence_root = playbook_root / "runs" / "current" / "evidence"
    rows: list[dict[str, Any]] = []
    if not evidence_root.exists():
        return rows
    for path in sorted(candidate for candidate in evidence_root.rglob("*") if candidate.is_file()):
        rel = path.relative_to(playbook_root).as_posix()
        rows.append(
            {
                "id": stable_uuid(run_db_id, "evidence", rel),
                "run_id": run_db_id,
                "evidence_type": infer_evidence_type(path),
                "path": rel,
                "summary": path.name,
                "captured_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
    return rows


def evidence_id_by_path(evidence_items: list[dict[str, Any]]) -> dict[str, str]:
    return {row["path"]: row["id"] for row in evidence_items}


def first_evidence_id_by_type(evidence_items: list[dict[str, Any]], evidence_type: str) -> str | None:
    for row in evidence_items:
        if row["evidence_type"] == evidence_type:
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
) -> list[dict[str, Any]]:
    evidence = status_payload.get("evidence", {})
    completion = status_payload.get("completion", {})
    evidence_paths = evidence_id_by_path(evidence_items)
    integration_review = artifact_by_suffix(artifacts, "runs/current/artifacts/architecture/integration-review.md")
    acceptance_review = artifact_by_suffix(artifacts, "runs/current/artifacts/product/acceptance-review.md")

    checks = [
        (
            "completion_gate",
            CHECK_STATUS_MAP.get(completion.get("complete")),
            None,
            None,
            json.dumps(completion),
        ),
        (
            "phase5_ready",
            CHECK_STATUS_MAP.get(status_payload.get("phase5_ready")),
            "phase-5-parallel-implementation",
            None,
            json.dumps(status_payload.get("phase5_blockers", [])),
        ),
        (
            "contract_samples_present",
            CHECK_STATUS_MAP.get(evidence.get("contract_samples_exists")),
            "phase-6-integration-review",
            evidence_paths.get("runs/current/evidence/contract-samples.md"),
            None,
        ),
        (
            "recovery_log_present",
            "pass" if evidence.get("recovery_log_exists") else "warning",
            None,
            evidence_paths.get("runs/current/evidence/orchestrator/recovery-log.md"),
            None,
        ),
        (
            "backend_tests_evidence",
            "pass" if first_evidence_id_by_type(evidence_items, "backend_tests") else "warning",
            "phase-6-integration-review",
            first_evidence_id_by_type(evidence_items, "backend_tests"),
            None,
        ),
        (
            "frontend_tests_evidence",
            "pass" if first_evidence_id_by_type(evidence_items, "frontend_tests") else "warning",
            "phase-6-integration-review",
            first_evidence_id_by_type(evidence_items, "frontend_tests"),
            None,
        ),
        (
            "e2e_tests_evidence",
            "pass" if first_evidence_id_by_type(evidence_items, "e2e_tests") else "warning",
            "phase-6-integration-review",
            first_evidence_id_by_type(evidence_items, "e2e_tests"),
            None,
        ),
        (
            "integration_review_artifact",
            "pass" if integration_review and integration_review["status"] in {"ready_for_handoff", "approved"} else "warning",
            "phase-6-integration-review",
            None,
            integration_review["status"] if integration_review else "missing",
        ),
        (
            "acceptance_review_gate",
            "pass" if acceptance_review and acceptance_review["status"] == "approved" else "fail",
            "phase-7-product-acceptance",
            None,
            acceptance_review["status"] if acceptance_review else "missing",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for name, status, phase_code, evidence_item_id, details in checks:
        rows.append(
            {
                "id": stable_uuid(run_db_id, "verification", name),
                "run_id": run_db_id,
                "phase_code": phase_code,
                "role_code": None,
                "check_name": name,
                "status": status or "unknown",
                "evidence_item_id": evidence_item_id,
                "details": details,
                "started_at": None,
                "finished_at": utcnow(),
            }
        )
    return rows


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
            }
        )
    return rows


def build_blockers(
    run_db_id: str,
    status_payload: dict[str, Any],
    artifacts: list[dict[str, Any]],
    handoffs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def append_blocker(
        source_type: str,
        source_id: str,
        title: str,
        *,
        phase_code: str | None = None,
        role_code: str | None = None,
        severity: str = "medium",
        details: dict[str, Any] | None = None,
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
                "severity": severity,
                "title": title,
                "details": json.dumps(details or {}, sort_keys=True) if details is not None else None,
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
    roles = [
        {"code": code, "display_name": display_name, "is_core": is_core}
        for code, display_name, is_core in ROLE_DEFS
    ]
    phases = [
        {"code": code, "ordinal": ordinal, "name": name, "lead_role_code": lead, "weight": weight}
        for code, ordinal, name, lead, weight in PHASE_DEFS
    ]

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
    current_phase_code = status_payload.get("current_phase_code")

    packages, artifacts, dependencies = collect_artifacts(playbook_root, run_db_id)
    handoffs = collect_handoffs(playbook_root, run_db_id)
    evidence_items = collect_evidence(playbook_root, run_db_id)
    agent_turns = collect_agent_turns(playbook_root, run_db_id)
    verification_checks = collect_verification_checks(run_db_id, status_payload, evidence_items, artifacts)
    blockers = build_blockers(run_db_id, status_payload, artifacts, handoffs)
    dashboard_snapshot = collect_dashboard_snapshot(run_db_id, status_payload, blockers, package_summary_from_rows(packages))
    phase_rows = build_phase_rows(run_db_id, status_payload)

    run_number = int(re.sub(r"\D", "", run_id_raw) or "1")
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
        "current_phase_code": current_phase_code,
        "overall_progress": float(status_payload.get("overall_progress", 0.0)),
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
        "run_phase_status": phase_rows,
        "artifact_packages": packages,
        "artifacts": artifacts,
        "artifact_dependencies": dependencies,
        "handoff_messages": handoffs,
        "blockers": blockers,
        "evidence_items": evidence_items,
        "verification_checks": verification_checks,
        "agent_turns": agent_turns,
        "dashboard_snapshot": dashboard_snapshot,
        "status_payload": status_payload,
    }
