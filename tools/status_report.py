#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from check_completion import collect_blockers
from check_orchestrator_liveness import collect_liveness, latest_log_activity, latest_worker_heartbeat
from check_phase5_ready import collect_phase5_blockers
from orchestrator_common import (
    RUN_ARTIFACT_TEMPLATE_DIRS,
    iter_required_artifact_templates,
    parse_metadata_block,
    resolve_repo_root,
)

RUN_DASHBOARD_SRC = Path(__file__).resolve().parents[1] / "run_dashboard" / "src"
if str(RUN_DASHBOARD_SRC) not in sys.path:
    sys.path.insert(0, str(RUN_DASHBOARD_SRC))

from run_dashboard.status_contract import (
    compute_overall_progress,
    normalize_status_report_payload,
    readiness_ratio,
    should_include_artifact_file,
    summarize_package_status,
)


ROLE_ORDER = (
    "product_manager",
    "architect",
    "frontend",
    "backend",
    "qa",
    "ceo",
    "deployment",
)

ARTIFACT_AREAS = (
    "product",
    "architecture",
    "ux",
    "backend-design",
    "devops",
)

PHASE_LABELS = {
    "complete": "Complete",
    "phase-0-intake-and-framing": "Phase 0 - Intake and framing",
    "phase-1-product-definition": "Phase 1 - Product definition",
    "phase-2-architecture-contract": "Phase 2 - Architecture and contract",
    "phase-3-ux-and-interaction-design": "Phase 3 - UX and interaction design",
    "phase-4-backend-design-and-rules-mapping": "Phase 4 - Backend design and rules mapping",
    "phase-5-parallel-implementation": "Phase 5 - Parallel implementation",
    "phase-6-integration-review": "Phase 6 - Integration review",
    "phase-7-product-acceptance": "Phase 7 - Product acceptance",
    "phase-8-qa-pre-delivery-validation": "Phase 8 - QA pre-delivery validation",
    "phase-I0-baseline-alignment": "Phase I0 - Baseline alignment",
    "phase-I1-change-intake-and-triage": "Phase I1 - Change intake and triage",
    "phase-I2-product-and-scope-delta": "Phase I2 - Product and scope delta",
    "phase-I3-architecture-and-contract-delta": "Phase I3 - Architecture and contract delta",
    "phase-I4-design-delta": "Phase I4 - Design delta",
    "phase-I5-implementation-delta": "Phase I5 - Implementation delta",
    "phase-I6-integration-and-regression-review": "Phase I6 - Integration and regression review",
    "phase-I7-change-acceptance": "Phase I7 - Change acceptance",
}

CHANGE_RUN_MODES = {"iterative-change-run", "app-only-hotfix"}
CHANGE_PHASE_ORDER = (
    "phase-I1-change-intake-and-triage",
    "phase-I2-product-and-scope-delta",
    "phase-I3-architecture-and-contract-delta",
    "phase-I4-design-delta",
    "phase-I5-implementation-delta",
    "phase-I6-integration-and-regression-review",
    "phase-I7-change-acceptance",
)
CHANGE_GATE_ALIASES = {
    "phase-I5-frontend-implementation-delta": "phase-I5-implementation-delta",
    "phase-I5-backend-implementation-delta": "phase-I5-implementation-delta",
}

STATUS_SCORES = {
    "missing": 0.0,
    "stub": 0.0,
    "draft": 0.45,
    "ready-for-handoff": 0.8,
    "approved": 1.0,
    "blocked": 0.2,
    "superseded": 0.3,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def count_markdown_files(path: Path) -> int:
    if not path.exists():
        return 0
    return len([candidate for candidate in path.glob("*.md") if candidate.is_file()])


def oldest_markdown_name(path: Path) -> str:
    if not path.exists():
        return ""
    names = sorted(candidate.name for candidate in path.glob("*.md") if candidate.is_file())
    return names[0] if names else ""


def latest_file_mtime(path: Path) -> str:
    if not path.exists():
        return ""
    latest_ts = 0.0
    for candidate in path.rglob("*"):
        if not candidate.is_file():
            continue
        try:
            latest_ts = max(latest_ts, candidate.stat().st_mtime)
        except OSError:
            continue
    if latest_ts <= 0.0:
        return ""
    return datetime.fromtimestamp(latest_ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def active_change_root(repo_root: Path, run_status: dict[str, Any]) -> Path | None:
    change_id = str(run_status.get("change_id", "")).strip()
    if not change_id:
        return None
    return repo_root / "runs" / "current" / "changes" / change_id


def change_promotion_accepted(change_root: Path | None) -> bool:
    if change_root is None:
        return False
    promotion_path = change_root / "promotion.yaml"
    if not promotion_path.exists():
        return False
    text = promotion_path.read_text(encoding="utf-8")
    match = re.search(r"^accepted_at:\s*['\"]?([^'\"]*)['\"]?\s*$", text, flags=re.MULTILINE)
    if not match:
        return False
    return bool(match.group(1).strip())


def change_run_pending(repo_root: Path, run_status: dict[str, Any]) -> bool:
    mode = str(run_status.get("mode", "")).strip()
    if mode not in CHANGE_RUN_MODES:
        return False
    if str(run_status.get("status", "")).strip() == "complete":
        return False
    return not change_promotion_accepted(active_change_root(repo_root, run_status))


def parse_reopened_gates(change_root: Path | None) -> list[str]:
    if change_root is None:
        return []
    reopened_path = change_root / "reopened-gates.md"
    if not reopened_path.exists():
        return []
    text = reopened_path.read_text(encoding="utf-8")
    candidates = re.findall(r"phase-I[0-7][A-Za-z0-9-]*", text)
    ordered: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = CHANGE_GATE_ALIASES.get(candidate, candidate)
        if normalized not in CHANGE_PHASE_ORDER:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def role_has_pending_work(roles: dict[str, dict[str, Any]], role: str) -> bool:
    payload = roles.get(role, {})
    return bool(payload.get("inbox_count", 0) or payload.get("inflight_count", 0))


def compute_change_run_phase(
    repo_root: Path,
    run_status: dict[str, Any],
    roles: dict[str, dict[str, Any]],
) -> str:
    if role_has_pending_work(roles, "product_manager"):
        return "phase-I1-change-intake-and-triage"

    reopened_gates = parse_reopened_gates(active_change_root(repo_root, run_status))
    if not reopened_gates:
        return "phase-I2-product-and-scope-delta"

    if role_has_pending_work(roles, "architect"):
        for phase in ("phase-I3-architecture-and-contract-delta", "phase-I4-design-delta"):
            if phase in reopened_gates:
                return phase

    if role_has_pending_work(roles, "frontend") or role_has_pending_work(roles, "backend"):
        for phase in ("phase-I5-implementation-delta", "phase-I6-integration-and-regression-review"):
            if phase in reopened_gates:
                return phase

    if role_has_pending_work(roles, "qa"):
        return "phase-I7-change-acceptance"

    for phase in CHANGE_PHASE_ORDER:
        if phase == "phase-I2-product-and-scope-delta" and any(
            candidate != "phase-I2-product-and-scope-delta" for candidate in reopened_gates
        ):
            continue
        if phase in reopened_gates:
            return phase
    return "phase-I7-change-acceptance"


def queue_summary(repo_root: Path) -> dict[str, dict[str, Any]]:
    role_state_root = repo_root / "runs" / "current" / "role-state"
    summary: dict[str, dict[str, Any]] = {}
    role_names = list(ROLE_ORDER)
    role_aliases = {
        "devops": "deployment",
    }
    if role_state_root.exists():
        for role_dir in sorted(path.name for path in role_state_root.iterdir() if path.is_dir()):
            normalized = role_aliases.get(role_dir, role_dir)
            if normalized not in role_names:
                role_names.append(normalized)

    for role in role_names:
        physical_roles = [role]
        if role == "deployment":
            physical_roles.append("devops")

        inbox_count = 0
        inflight_count = 0
        processed_count = 0
        oldest_inbox = ""
        context_exists = False
        exists = False

        for physical_role in physical_roles:
            role_root = role_state_root / physical_role
            if not role_root.exists():
                continue
            exists = True
            inbox_count += count_markdown_files(role_root / "inbox")
            inflight_count += count_markdown_files(role_root / "inflight")
            processed_count += count_markdown_files(role_root / "processed")
            if not oldest_inbox:
                oldest_inbox = oldest_markdown_name(role_root / "inbox")
            context_exists = context_exists or (role_root / "context.md").exists()

        summary[role] = {
            "exists": exists,
            "inbox_count": inbox_count,
            "inflight_count": inflight_count,
            "processed_count": processed_count,
            "oldest_inbox": oldest_inbox,
            "context_exists": context_exists,
        }
    return summary


def run_artifact_rel_path(artifact_dir: str, template_path: Path) -> str:
    return f"runs/current/artifacts/{artifact_dir}/{template_path.name}"


def artifact_status(repo_root: Path, rel_path: str) -> str:
    path = repo_root / rel_path
    if not path.exists():
        return "missing"
    status = str(parse_metadata_block(path).get("status", "")).strip()
    return status or "unknown"


def phase_requirements(repo_root: Path) -> dict[str, list[str]]:
    by_phase: dict[str, list[str]] = {}
    for artifact_dir, template_path in iter_required_artifact_templates(repo_root):
        metadata = parse_metadata_block(template_path)
        phase = str(metadata.get("phase", "")).strip()
        if not phase:
            continue
        by_phase.setdefault(phase, []).append(run_artifact_rel_path(artifact_dir, template_path))
    return {phase: sorted(paths) for phase, paths in sorted(by_phase.items())}


def phase_summary(repo_root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    by_phase = phase_requirements(repo_root)
    for phase, paths in by_phase.items():
        statuses = {path: artifact_status(repo_root, path) for path in paths}
        missing = [path for path, status in statuses.items() if status == "missing"]
        blocked = [path for path, status in statuses.items() if status == "blocked"]
        stub = [path for path, status in statuses.items() if status == "stub"]
        draft = [path for path, status in statuses.items() if status in {"draft", "superseded", "unknown"}]
        scores = [STATUS_SCORES.get(status, 0.2) for status in statuses.values()]
        score = round(sum(scores) / len(scores), 3) if scores else 0.0

        if blocked:
            state = "blocked"
        elif paths and not missing and not stub and all(
            statuses[path] in {"ready-for-handoff", "approved"} for path in paths
        ):
            state = "complete"
        elif any(status != "missing" for status in statuses.values()):
            state = "in-progress"
        else:
            state = "not-started"

        result[phase] = {
            "label": PHASE_LABELS.get(phase, phase),
            "state": state,
            "score": score,
            "expected_count": len(paths),
            "missing": missing,
            "blocked": blocked,
            "stub": stub,
            "draft": draft,
        }
    return result


def artifact_area_summary(repo_root: Path) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for area in ARTIFACT_AREAS:
        area_root = repo_root / "runs" / "current" / "artifacts" / area
        counter: Counter[str] = Counter()
        files: list[str] = []
        if area_root.exists():
            for candidate in sorted(area_root.rglob("*.md")):
                if not should_include_artifact_file(candidate.relative_to(area_root)):
                    continue
                files.append(candidate.relative_to(repo_root).as_posix())
                counter[artifact_status(repo_root, candidate.relative_to(repo_root).as_posix())] += 1
        summaries[area] = {
            "exists": area_root.exists(),
            "file_count": len(files),
            "counts": dict(counter),
            "overall_status": summarize_package_status(counter),
            "readiness_ratio": readiness_ratio(counter),
            "latest_mtime": latest_file_mtime(area_root),
        }
    return summaries


def evidence_summary(repo_root: Path) -> dict[str, Any]:
    evidence_root = repo_root / "runs" / "current" / "evidence"
    orchestrator_root = evidence_root / "orchestrator"
    log_time, log_line = latest_log_activity(orchestrator_root / "logs" / "orchestrator.log")
    heartbeat_time, heartbeat_source = latest_worker_heartbeat(repo_root / "runs" / "current" / "orchestrator" / "workers")
    latest_activity = ""
    latest_source = ""
    if log_time and heartbeat_time:
        if log_time >= heartbeat_time:
            latest_activity = log_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            latest_source = log_line
        else:
            latest_activity = heartbeat_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            latest_source = heartbeat_source
    elif log_time:
        latest_activity = log_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        latest_source = log_line
    elif heartbeat_time:
        latest_activity = heartbeat_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        latest_source = heartbeat_source

    return {
        "exists": evidence_root.exists(),
        "latest_activity": latest_activity,
        "latest_activity_source": latest_source,
        "contract_samples_exists": (evidence_root / "contract-samples.md").exists(),
        "recovery_log_exists": (orchestrator_root / "recovery-log.md").exists(),
        "jsonl_file_count": len(list((orchestrator_root / "jsonl").glob("*.jsonl"))) if (orchestrator_root / "jsonl").exists() else 0,
    }


def compute_current_phase(
    repo_root: Path,
    run_status: dict[str, Any],
    roles: dict[str, dict[str, Any]],
    phases: dict[str, dict[str, Any]],
    completion_complete: bool,
) -> str:
    explicit = str(run_status.get("current_phase", "")).strip()
    if change_run_pending(repo_root, run_status):
        if explicit:
            return explicit
        return compute_change_run_phase(repo_root, run_status, roles)
    if completion_complete or str(run_status.get("status", "")).strip() == "complete":
        return "complete"
    if explicit:
        return explicit
    ordered = [
        "phase-0-intake-and-framing",
        "phase-1-product-definition",
        "phase-2-architecture-contract",
        "phase-3-ux-and-interaction-design",
        "phase-4-backend-design-and-rules-mapping",
        "phase-5-parallel-implementation",
        "phase-6-integration-review",
        "phase-7-product-acceptance",
        "phase-8-qa-pre-delivery-validation",
    ]
    for phase in ordered:
        if phase == "phase-5-parallel-implementation":
            continue
        state = phases.get(phase, {}).get("state")
        if state != "complete":
            return phase
    return "phase-8-qa-pre-delivery-validation"


def stage_progress(phases: dict[str, dict[str, Any]], phase5_ready: bool) -> dict[str, Any]:
    build_state = "not-started"
    if phase5_ready:
        pre_integration = phases.get("phase-6-integration-review", {}).get("state") not in {"in-progress", "complete", "blocked"}
        build_state = "in-progress" if pre_integration else "complete"

    return {
        "discovery": {
            "score": round(
                (
                    phases.get("phase-0-intake-and-framing", {}).get("score", 0.0)
                    + phases.get("phase-1-product-definition", {}).get("score", 0.0)
                )
                / 2.0,
                3,
            ),
        },
        "architecture": {"score": phases.get("phase-2-architecture-contract", {}).get("score", 0.0)},
        "design": {
            "score": round(
                (
                    phases.get("phase-3-ux-and-interaction-design", {}).get("score", 0.0)
                    + phases.get("phase-4-backend-design-and-rules-mapping", {}).get("score", 0.0)
                )
                / 2.0,
                3,
            ),
        },
        "build": {"state": build_state, "phase5_ready": phase5_ready},
        "integration": {"score": phases.get("phase-6-integration-review", {}).get("score", 0.0)},
        "acceptance": {"score": phases.get("phase-7-product-acceptance", {}).get("score", 0.0)},
        "qa": {"score": phases.get("phase-8-qa-pre-delivery-validation", {}).get("score", 0.0)},
    }


def report_payload(repo_root: Path) -> dict[str, Any]:
    run_status = load_json(repo_root / "runs" / "current" / "orchestrator" / "run-status.json")
    roles = queue_summary(repo_root)
    workers = {}
    workers_root = repo_root / "runs" / "current" / "orchestrator" / "workers"
    if workers_root.exists():
        for path in sorted(workers_root.glob("*.json")):
            workers[path.stem] = load_json(path)

    phases = phase_summary(repo_root)
    phase5_blockers = collect_phase5_blockers(repo_root)
    completion_blockers = collect_blockers(repo_root)
    change_pending = change_run_pending(repo_root, run_status)
    if change_pending:
        change_root = active_change_root(repo_root, run_status)
        blocker_path = change_root / "promotion.yaml" if change_root else repo_root / "runs" / "current" / "orchestrator" / "run-status.json"
        completion_blockers = list(completion_blockers)
        completion_blockers.append(
            {
                "kind": "active-change-run-pending",
                "path": blocker_path.relative_to(repo_root).as_posix(),
                "phase": "phase-I1-change-intake-and-triage",
                "reason": "active iteration/change run pending; Product Manager must confirm reopened phases before the run can be considered complete",
            }
        )
    current_phase = compute_current_phase(repo_root, run_status, roles, phases, not completion_blockers)
    payload = {
        "generated_at": utc_now(),
        "repo_root": str(repo_root),
        "run_status": run_status,
        "current_phase_code": current_phase,
        "current_phase": {
            "key": current_phase,
            "label": PHASE_LABELS.get(current_phase, current_phase),
        },
        "overall_progress": compute_overall_progress(phases, not completion_blockers),
        "phase5_ready": not phase5_blockers,
        "phase5_blockers": phase5_blockers,
        "completion": {
            "complete": not completion_blockers,
            "blockers": completion_blockers,
        },
        "roles": roles,
        "workers": workers,
        "artifacts": artifact_area_summary(repo_root),
        "phases": phases,
        "stages": stage_progress(phases, not phase5_blockers),
        "evidence": evidence_summary(repo_root),
        "liveness": collect_liveness(repo_root),
        "app": {
            "exists": (repo_root / "app").exists(),
            "latest_mtime": latest_file_mtime(repo_root / "app"),
        },
    }
    return normalize_status_report_payload(payload)


def format_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Run Status Report")
    lines.append("")
    lines.append(f"- generated_at: `{payload['generated_at']}`")
    lines.append(f"- run_status: `{payload['run_status'].get('status', 'unknown')}`")
    lines.append(f"- mode: `{payload['run_status'].get('mode', '')}`")
    lines.append(f"- current_phase: `{payload['current_phase']['label']}`")
    lines.append(f"- phase5_ready: `{payload['phase5_ready']}`")
    lines.append(f"- completion_complete: `{payload['completion']['complete']}`")
    lines.append("")

    lines.append("## Roles")
    lines.append("")
    lines.append("| Role | Inbox | Inflight | Processed | Oldest Inbox | Context |")
    lines.append("| --- | ---: | ---: | ---: | --- | --- |")
    for role, info in payload["roles"].items():
        lines.append(
            f"| `{role}` | {info['inbox_count']} | {info['inflight_count']} | {info['processed_count']} | "
            f"{info['oldest_inbox'] or ''} | {('yes' if info['context_exists'] else 'no')} |"
        )
    lines.append("")

    lines.append("## Phases")
    lines.append("")
    lines.append("| Phase | State | Score | Missing | Stub | Blocked |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: |")
    for phase_key in sorted(payload["phases"]):
        phase = payload["phases"][phase_key]
        lines.append(
            f"| `{phase['label']}` | {phase['state']} | {phase['score']:.3f} | "
            f"{len(phase['missing'])} | {len(phase['stub'])} | {len(phase['blocked'])} |"
        )
    lines.append("")

    lines.append("## Completion Blockers")
    lines.append("")
    blockers = payload["completion"]["blockers"]
    if not blockers:
        lines.append("- none")
    else:
        for blocker in blockers[:20]:
            item = f"- {blocker['reason']}: `{blocker['path']}`"
            if blocker.get("owner"):
                item += f" [owner={blocker['owner']}]"
            if blocker.get("phase"):
                item += f" [phase={blocker['phase']}]"
            if blocker.get("alias_hint"):
                item += f" [likely_alias={blocker['alias_hint']}]"
            lines.append(item)
    lines.append("")

    lines.append("## Evidence")
    lines.append("")
    lines.append(f"- latest_activity: `{payload['evidence']['latest_activity'] or ''}`")
    lines.append(f"- latest_activity_source: `{payload['evidence']['latest_activity_source'] or ''}`")
    lines.append(f"- contract_samples_exists: `{payload['evidence']['contract_samples_exists']}`")
    lines.append(f"- recovery_log_exists: `{payload['evidence']['recovery_log_exists']}`")
    lines.append(f"- jsonl_file_count: `{payload['evidence']['jsonl_file_count']}`")
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root or Path.cwd())
    payload = report_payload(repo_root)
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_markdown(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
