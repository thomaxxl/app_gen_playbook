#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import yaml

from check_completion import collect_blockers
from orchestrator_common import (
    DISPLAY_TO_RUNTIME,
    CORE_DISPLAY_ROLES,
    RUN_ARTIFACT_TEMPLATE_DIRS,
    all_role_state_dirs,
    iter_required_artifact_templates,
    parse_message_headers,
    parse_message_sections,
    parse_metadata_block,
    preferred_role_state_dir,
    resolve_repo_root,
)


PHASE_ORDER = {
    "phase-0-intake-and-framing": 0,
    "phase-1-product-definition": 1,
    "phase-2-architecture-contract": 2,
    "phase-3-ux-and-interaction-design": 3,
    "phase-4-backend-design-and-rules-mapping": 4,
    "phase-5-parallel-implementation": 5,
    "phase-6-integration-review": 6,
    "phase-7-product-acceptance": 7,
}

EARLY_PHASES = {
    "phase-0-intake-and-framing",
    "phase-1-product-definition",
    "phase-2-architecture-contract",
    "phase-3-ux-and-interaction-design",
    "phase-4-backend-design-and-rules-mapping",
}
EARLY_PHASE_FRONTIERS: tuple[tuple[str, ...], ...] = (
    ("phase-0-intake-and-framing",),
    ("phase-1-product-definition",),
    ("phase-2-architecture-contract",),
    ("phase-3-ux-and-interaction-design", "phase-4-backend-design-and-rules-mapping"),
)

ROLE_LABELS = {
    "product_manager": "product_manager",
    "architect": "architect",
    "frontend": "frontend",
    "backend": "backend",
    "deployment": "devops",
}

ROLE_PURPOSE = {
    "product_manager": (
        "restore progress by completing missing canonical product artifacts and "
        "issuing the downstream handoff required by the next gate"
    ),
    "architect": (
        "restore progress by completing missing canonical architecture artifacts "
        "or performing the late-phase architecture review gate"
    ),
    "frontend": (
        "restore progress by completing missing canonical UX or frontend-owned "
        "phase artifacts and handing them back to Architect"
    ),
    "backend": (
        "restore progress by completing missing canonical backend-design "
        "artifacts or backend-owned implementation follow-up"
    ),
    "deployment": (
        "restore progress by completing missing optional devops artifacts when "
        "the deployment lane is active"
    ),
}

RECOVERABLE_NON_FINAL_STATUSES = {"blocked", "draft", "in-progress", "interrupted", "superseded", "unknown"}
APP_IMPLEMENTATION_NEEDS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "architect",
        "app/README.md",
        "missing",
        (
            "playbook/process/phases/phase-5-parallel-implementation.md",
            "playbook/process/playbook-execution-outputs.md",
            "templates/app/project/README.app.md",
        ),
    ),
    (
        "product_manager",
        "app/BUSINESS_RULES.md",
        "missing",
        (
            "playbook/process/phases/phase-5-parallel-implementation.md",
            "playbook/process/playbook-execution-outputs.md",
            "templates/app/project/BUSINESS_RULES.app.md",
        ),
    ),
    (
        "deployment",
        "app/.gitignore",
        "missing",
        (
            "playbook/task-bundles/deployment.yaml",
            "playbook/process/phases/phase-5-parallel-implementation.md",
            "templates/app/project/.gitignore.md",
        ),
    ),
    (
        "deployment",
        "app/install.sh",
        "missing",
        (
            "playbook/task-bundles/deployment.yaml",
            "playbook/process/phases/phase-5-parallel-implementation.md",
            "templates/app/project/install.sh.md",
        ),
    ),
    (
        "deployment",
        "app/run.sh",
        "missing",
        (
            "playbook/task-bundles/deployment.yaml",
            "playbook/process/phases/phase-5-parallel-implementation.md",
            "templates/app/project/run.sh.md",
        ),
    ),
    (
        "backend",
        "app/reference/admin.yaml",
        "missing",
        (
            "playbook/task-bundles/backend-implementation.yaml",
            "playbook/process/phases/phase-5-parallel-implementation.md",
            "templates/app/reference/admin.yaml.md",
        ),
    ),
    (
        "backend",
        "app/backend/requirements.txt",
        "missing",
        (
            "playbook/task-bundles/backend-implementation.yaml",
            "playbook/process/phases/phase-5-parallel-implementation.md",
            "templates/app/backend/requirements.txt.md",
        ),
    ),
    (
        "backend",
        "app/backend/run.py",
        "missing",
        (
            "playbook/task-bundles/backend-implementation.yaml",
            "playbook/process/phases/phase-5-parallel-implementation.md",
            "templates/app/backend/run.py.md",
        ),
    ),
    (
        "backend",
        "app/rules/rules.py",
        "missing",
        (
            "playbook/task-bundles/backend-implementation.yaml",
            "playbook/process/phases/phase-5-parallel-implementation.md",
            "templates/app/rules/rules.py.md",
        ),
    ),
    (
        "frontend",
        "app/frontend/package.json",
        "missing",
        (
            "playbook/task-bundles/frontend-implementation.yaml",
            "playbook/process/phases/phase-5-parallel-implementation.md",
            "templates/app/frontend/package.json.md",
        ),
    ),
    (
        "frontend",
        "app/frontend/vite.config.ts",
        "missing",
        (
            "playbook/task-bundles/frontend-implementation.yaml",
            "playbook/process/phases/phase-5-parallel-implementation.md",
            "templates/app/frontend/vite.config.ts.md",
        ),
    ),
)

COMPLETION_BLOCKER_RECOVERY_PHASE_OVERRIDES = {
    # Completion can observe this from phase 6, but repairing generated backend
    # source is phase-5 implementation work.
    "app/backend/src": "phase-5-parallel-implementation",
    "app/backend/src/my_app": "phase-5-parallel-implementation",
}
ACTIONABLE_COMPLETION_BLOCKER_KINDS = {
    "missing-generated-app-output",
    "missing-required-evidence-output",
    "required-evidence-output-placeholder",
    "contract-samples-unstructured",
    "ui-preview-manifest-unstructured",
    "ui-preview-images-missing",
    "ui-preview-content-validation-missing",
    "ui-preview-signoff-missing",
    "ui-preview-review-conclusion-missing",
    "ui-preview-fallback-invalid",
    "backend-orm-safrs-audit-failed",
}
REQUIRED_EVIDENCE_NEEDS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "architect",
        "runs/current/evidence/contract-samples.md",
        "missing",
        (
            "playbook/task-bundles/integration-review.yaml",
            "playbook/process/phases/phase-6-integration-review.md",
        ),
    ),
    (
        "architect",
        "runs/current/evidence/frontend-usability.md",
        "missing",
        (
            "playbook/task-bundles/integration-review.yaml",
            "playbook/process/phases/phase-6-integration-review.md",
        ),
    ),
    (
        "architect",
        "runs/current/evidence/ui-previews/manifest.md",
        "missing",
        (
            "playbook/task-bundles/integration-review.yaml",
            "playbook/process/phases/phase-6-integration-review.md",
        ),
    ),
    (
        "architect",
        "runs/current/evidence/quality/crud-matrix.md",
        "missing",
        (
            "playbook/task-bundles/integration-review.yaml",
            "playbook/process/phases/phase-6-integration-review.md",
            "playbook/process/quality-gates.md",
        ),
    ),
    (
        "architect",
        "runs/current/evidence/quality/data-sourcing-audit.md",
        "missing",
        (
            "playbook/task-bundles/integration-review.yaml",
            "playbook/process/phases/phase-6-integration-review.md",
            "playbook/process/quality-gates.md",
        ),
    ),
    (
        "architect",
        "runs/current/evidence/quality/seed-data-audit.md",
        "missing",
        (
            "playbook/task-bundles/integration-review.yaml",
            "playbook/process/phases/phase-6-integration-review.md",
            "playbook/process/quality-gates.md",
        ),
    ),
    (
        "architect",
        "runs/current/evidence/quality/ui-copy-audit.md",
        "missing",
        (
            "playbook/task-bundles/integration-review.yaml",
            "playbook/process/phases/phase-6-integration-review.md",
            "playbook/process/quality-gates.md",
        ),
    ),
    (
        "architect",
        "runs/current/evidence/quality/test-results.md",
        "missing",
        (
            "playbook/task-bundles/integration-review.yaml",
            "playbook/process/phases/phase-6-integration-review.md",
            "playbook/process/quality-gates.md",
        ),
    ),
    (
        "architect",
        "runs/current/evidence/quality/quality-summary.md",
        "missing",
        (
            "playbook/task-bundles/integration-review.yaml",
            "playbook/process/phases/phase-6-integration-review.md",
            "playbook/process/quality-gates.md",
        ),
    ),
    (
        "architect",
        "runs/current/evidence/quality/coverage-report.md",
        "missing",
        (
            "playbook/task-bundles/integration-review.yaml",
            "playbook/process/phases/phase-6-integration-review.md",
            "playbook/process/quality-gates.md",
        ),
    ),
    (
        "architect",
        "runs/current/evidence/quality/review-plan.json",
        "missing",
        (
            "playbook/task-bundles/integration-review.yaml",
            "playbook/process/phases/phase-3-ux-and-interaction-design.md",
            "playbook/process/phases/phase-6-integration-review.md",
            "playbook/process/quality-gates.md",
        ),
    ),
)
RECOVERY_REQUEUE_COOLDOWN = timedelta(minutes=30)
SOURCE_SCOPE_PATH_PATTERN = re.compile(r"`((?:specs|playbook|tools|scripts|skills)/[^`]+)`")
SOURCE_SCOPE_INLINE_PATH_PATTERN = re.compile(r"((?:specs|playbook|tools|scripts|skills)/[A-Za-z0-9_./-]+)")
SOURCE_SCOPE_NEGATED_PATH_PATTERN = re.compile(
    r"no change (?:is )?required in `((?:specs|playbook|tools|scripts|skills)/[^`]+)`",
    re.IGNORECASE,
)
SOURCE_SCOPE_HINT_PATTERN = re.compile(
    r"(source[- ]scope|source[- ]repair|source-maintenance|write[- ]scope|playbook-maintenance|normative source)",
    re.IGNORECASE,
)

PHASE_REQUIRED_READS = {
    "phase-1-product-definition": (
        "playbook/task-bundles/phase-1-product-definition.yaml",
        "playbook/process/phases/phase-1-product-definition.md",
        "specs/product/README.md",
    ),
    "phase-2-architecture-contract": (
        "playbook/task-bundles/phase-2-architecture-contract.yaml",
        "playbook/process/phases/phase-2-architecture-contract.md",
        "specs/architecture/README.md",
    ),
    "phase-3-ux-and-interaction-design": (
        "playbook/task-bundles/ux-design.yaml",
        "playbook/process/phases/phase-3-ux-and-interaction-design.md",
        "specs/ux/README.md",
    ),
    "phase-4-backend-design-and-rules-mapping": (
        "playbook/task-bundles/backend-design.yaml",
        "playbook/process/phases/phase-4-backend-design-and-rules-mapping.md",
        "specs/backend-design/README.md",
    ),
    "phase-6-integration-review": (
        "playbook/task-bundles/integration-review.yaml",
        "playbook/process/phases/phase-6-integration-review.md",
        "specs/architecture/integration-review.md",
    ),
    "phase-7-product-acceptance": (
        "playbook/task-bundles/acceptance-review.yaml",
        "playbook/process/phases/phase-7-product-acceptance.md",
        "specs/product/acceptance-review.md",
    ),
}


@dataclass(frozen=True)
class ArtifactNeed:
    role: str
    phase: str
    path: Path
    reason: str
    extra_reads: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceScopeEscalation:
    topic_slug: str
    required_reads: tuple[str, ...]
    requested_paths: tuple[str, ...]
    blocking_issues: tuple[str, ...]
    message_paths: tuple[Path, ...]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def note_timestamp(path: Path) -> datetime | None:
    stem, _, _ = path.name.partition("-from-")
    try:
        return datetime.strptime(stem, "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def active_core_roles() -> tuple[str, ...]:
    return tuple(DISPLAY_TO_RUNTIME[name] for name in CORE_DISPLAY_ROLES)


def role_pending(repo_root: Path, role: str) -> bool:
    for role_root in all_role_state_dirs(repo_root, role):
        for subdir in ("inbox", "inflight"):
            directory = role_root / subdir
            if directory.exists() and any(directory.glob("*.md")):
                return True
    return False


def orchestrator_pending(repo_root: Path) -> bool:
    role_root = repo_root / "runs" / "current" / "role-state" / "orchestrator"
    for subdir in ("inbox", "inflight"):
        directory = role_root / subdir
        if directory.exists() and any(directory.glob("*.md")):
            return True
    return False


def initial_input_pending(repo_root: Path) -> bool:
    for role_root in all_role_state_dirs(repo_root, "product_manager"):
        for subdir in ("inbox", "inflight"):
            if (role_root / subdir / "INPUT.md").exists():
                return True
    return False


def frontend_backend_quiescent(repo_root: Path) -> bool:
    return not role_pending(repo_root, "frontend") and not role_pending(repo_root, "backend")


def other_core_roles_quiescent(repo_root: Path, excluded_role: str) -> bool:
    for role in active_core_roles():
        if role == excluded_role:
            continue
        if role_pending(repo_root, role):
            return False
    return True


def iter_required_template_metadata(repo_root: Path) -> list[tuple[Path, dict[str, object]]]:
    pairs: list[tuple[Path, dict[str, object]]] = []
    for artifact_dir, template_path in iter_required_artifact_templates(repo_root):
        run_path = repo_root / "runs" / "current" / "artifacts" / artifact_dir / template_path.name
        metadata = parse_metadata_block(template_path)
        pairs.append((run_path, metadata))
    return pairs


def collect_artifact_needs(repo_root: Path) -> list[ArtifactNeed]:
    needs: list[ArtifactNeed] = []

    for run_path, template_meta in iter_required_template_metadata(repo_root):
        role = str(template_meta.get("owner", "")).strip()
        phase = str(template_meta.get("phase", "")).strip()
        if not role or role not in ROLE_LABELS or not phase:
            continue

        if not run_path.exists():
            needs.append(ArtifactNeed(role=role, phase=phase, path=run_path, reason="missing"))
            continue

        run_meta = parse_metadata_block(run_path)
        status = str(run_meta.get("status", "")).strip()
        if status == "stub":
            needs.append(ArtifactNeed(role=role, phase=phase, path=run_path, reason="stub"))
            continue

        if status in RECOVERABLE_NON_FINAL_STATUSES:
            needs.append(ArtifactNeed(role=role, phase=phase, path=run_path, reason=f"status={status}"))
            continue

        if run_path.name == "acceptance-review.md" and status != "approved":
            needs.append(ArtifactNeed(role=role, phase=phase, path=run_path, reason=f"status={status or 'missing-status'}"))

    return needs


def extra_reads_for_completion_blocker(path: str) -> tuple[str, ...]:
    for _, relative_path, _, extra_reads in APP_IMPLEMENTATION_NEEDS:
        if relative_path == path:
            return extra_reads

    for _, relative_path, _, extra_reads in REQUIRED_EVIDENCE_NEEDS:
        if relative_path == path:
            return extra_reads

    if path in {"app/backend/src", "app/backend/src/my_app"}:
        return (
            "playbook/task-bundles/backend-implementation.yaml",
            "playbook/process/phases/phase-5-parallel-implementation.md",
            "runs/current/artifacts/backend-design/resource-exposure-policy.md",
        )

    return ()


def recovery_phase_for_completion_blocker(path: str, phase: str) -> str:
    return COMPLETION_BLOCKER_RECOVERY_PHASE_OVERRIDES.get(path, phase)


def collect_completion_blocker_needs(repo_root: Path) -> list[ArtifactNeed]:
    needs: list[ArtifactNeed] = []

    for blocker in collect_blockers(repo_root):
        kind = str(blocker.get("kind", "")).strip()
        if kind not in ACTIONABLE_COMPLETION_BLOCKER_KINDS:
            continue

        role = str(blocker.get("owner", "")).strip()
        phase = str(blocker.get("phase", "")).strip()
        relative_path = str(blocker.get("path", "")).strip()
        reason = str(blocker.get("reason", "")).strip()
        if role not in ROLE_LABELS or not phase or not relative_path or not reason:
            continue

        needs.append(
            ArtifactNeed(
                role=role,
                phase=recovery_phase_for_completion_blocker(relative_path, phase),
                path=repo_root / relative_path,
                reason=reason,
                extra_reads=extra_reads_for_completion_blocker(relative_path),
            )
        )

    return needs


def template_path_for_need(repo_root: Path, need: ArtifactNeed) -> Path | None:
    parts = need.path.relative_to(repo_root).parts
    if len(parts) < 5:
        return None

    artifact_dir = parts[3]
    template_dir = RUN_ARTIFACT_TEMPLATE_DIRS.get(artifact_dir)
    if not template_dir:
        return None

    template_path = repo_root / template_dir / need.path.name
    if template_path.exists():
        return template_path
    return None


def should_recover_phase(repo_root: Path, phase: str, all_needs: list[ArtifactNeed], role: str) -> bool:
    if phase in EARLY_PHASES:
        for frontier in EARLY_PHASE_FRONTIERS:
            if any(need.phase in frontier for need in all_needs):
                return phase in frontier
        return False

    early_needs = [need for need in all_needs if need.phase in EARLY_PHASES]
    if early_needs:
        return False

    if phase == "phase-5-parallel-implementation":
        return True

    phase5_needs = [need for need in all_needs if need.phase == "phase-5-parallel-implementation"]
    if phase5_needs:
        return False

    if phase == "phase-6-integration-review":
        return frontend_backend_quiescent(repo_root)

    if phase == "phase-7-product-acceptance":
        phase6_needs = [need for need in all_needs if need.phase == "phase-6-integration-review"]
        if phase6_needs:
            return False
        return frontend_backend_quiescent(repo_root) and other_core_roles_quiescent(repo_root, role)

    return False


def select_recovery_targets(repo_root: Path) -> dict[str, list[ArtifactNeed]]:
    if initial_input_pending(repo_root):
        return {}

    needs = collect_artifact_needs(repo_root)
    needs.extend(collect_completion_blocker_needs(repo_root))
    targets: dict[str, list[ArtifactNeed]] = {}

    for role in ROLE_LABELS:
        if role_pending(repo_root, role):
            continue

        role_needs = [need for need in needs if need.role == role]
        if not role_needs:
            continue

        eligible = [need for need in role_needs if should_recover_phase(repo_root, need.phase, needs, role)]
        if role == "architect" and role_pending(repo_root, "deployment"):
            eligible = [need for need in eligible if need.path.name != "runtime-bom.md"]
        if not eligible:
            continue

        targets[role] = sorted(
            eligible,
            key=lambda need: (PHASE_ORDER.get(need.phase, 99), str(need.path), need.reason),
        )

    return targets


def _source_scope_paths(lines: list[str]) -> tuple[str, ...]:
    found: list[str] = []
    for line in lines:
        found.extend(SOURCE_SCOPE_PATH_PATTERN.findall(line))
    return tuple(_ordered_unique(found))


def _all_source_scope_paths(lines: list[str]) -> tuple[str, ...]:
    found: list[str] = []
    for line in lines:
        found.extend(SOURCE_SCOPE_PATH_PATTERN.findall(line))
        found.extend(SOURCE_SCOPE_INLINE_PATH_PATTERN.findall(line))
    return tuple(_ordered_unique(found))


def _negated_source_scope_paths(lines: list[str]) -> tuple[str, ...]:
    found: list[str] = []
    for line in lines:
        found.extend(SOURCE_SCOPE_NEGATED_PATH_PATTERN.findall(line))
    return tuple(_ordered_unique(found))


def _slugify_topic(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "source-contract-recovery"


def collect_source_scope_escalations(repo_root: Path) -> list[SourceScopeEscalation]:
    inbox_dir = repo_root / "runs" / "current" / "role-state" / "orchestrator" / "inbox"
    if not inbox_dir.exists():
        return []

    grouped: dict[tuple[str, ...], dict[str, object]] = {}
    for message_path in sorted(inbox_dir.glob("*.md")):
        message_text = message_path.read_text(encoding="utf-8")
        headers = parse_message_headers(message_text)
        if headers.get("to", "").strip().lower() != "orchestrator":
            continue
        sections = parse_message_sections(message_text, headers=headers)
        required_reads_section = [
            item
            for item in sections.get("required reads", [])
            if isinstance(item, str)
        ]
        requested_outputs = [
            item
            for item in sections.get("requested outputs", [])
            if isinstance(item, str)
        ]
        source_scope_context = [
            *requested_outputs,
            *required_reads_section,
            *[item for item in sections.get("notes", []) if isinstance(item, str)],
            *[item for item in sections.get("blocking issues", []) if isinstance(item, str)],
            *[item for item in sections.get("requested orchestrator action", []) if isinstance(item, str)],
            *[item for item in sections.get("current state", []) if isinstance(item, str)],
            headers.get("topic", ""),
            headers.get("purpose", ""),
        ]
        requested_paths = _source_scope_paths(requested_outputs)
        if not requested_paths and any(SOURCE_SCOPE_HINT_PATTERN.search(line) for line in source_scope_context if line):
            negated_paths = set(_negated_source_scope_paths(source_scope_context))
            candidate_paths = [
                path
                for path in _all_source_scope_paths(source_scope_context)
                if path not in negated_paths and (repo_root / path).exists()
            ]
            requested_paths = tuple(candidate_paths)
        if not requested_paths:
            continue

        key = requested_paths
        current = grouped.get(key)
        topic_slug = _slugify_topic(headers.get("topic", "source-contract-recovery"))
        required_reads = [
            message_path.relative_to(repo_root).as_posix(),
            *required_reads_section,
        ]
        blocking_issues = [
            item
            for item in sections.get("blocking issues", [])
            if isinstance(item, str)
        ]
        if current is None:
            grouped[key] = {
                "topic_slug": topic_slug,
                "required_reads": required_reads,
                "blocking_issues": blocking_issues,
                "message_paths": [message_path],
            }
            continue

        current["required_reads"] = _ordered_unique(list(current["required_reads"]) + required_reads)
        current["blocking_issues"] = _ordered_unique(list(current["blocking_issues"]) + blocking_issues)
        current["message_paths"] = list(current["message_paths"]) + [message_path]
        current["topic_slug"] = topic_slug

    escalations: list[SourceScopeEscalation] = []
    for requested_paths, payload in grouped.items():
        escalations.append(
            SourceScopeEscalation(
                topic_slug=str(payload["topic_slug"]),
                required_reads=tuple(_ordered_unique(list(payload["required_reads"]))),
                requested_paths=requested_paths,
                blocking_issues=tuple(_ordered_unique(list(payload["blocking_issues"]))),
                message_paths=tuple(payload["message_paths"]),
            )
        )
    return escalations


def format_source_scope_note(repo_root: Path, escalation: SourceScopeEscalation, change_id: str) -> str:
    required_reads = _ordered_unique(["runs/current/remarks.md", *escalation.required_reads, *escalation.requested_paths])

    lines: list[str] = [
        "from: orchestrator",
        "to: ceo",
        f"topic: {escalation.topic_slug}",
        "purpose: restore progress by resolving source-contract or playbook write-scope escalations that runtime roles cannot satisfy",
        f"change_id: {change_id}",
        "",
        "## Required Reads",
    ]
    for item in required_reads:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Requested Outputs",
            "- repair the normative source-contract or playbook files listed below using the CEO write boundary",
        ]
    )
    for item in escalation.requested_paths:
        lines.append(f"- edit `{item}`")
    lines.extend(
        [
            "- if the source contract is repaired, issue the downstream handoff needed to unblock the affected runtime role",
            "- do not route this contradiction back into the same blocked runtime write boundary unchanged",
            "",
            "## Dependencies",
            "- CEO/playbook-maintenance write scope",
            "",
            "## Gate Status",
            "- blocked",
            "",
            "## Blocking Issues",
        ]
    )
    if escalation.blocking_issues:
        for item in escalation.blocking_issues:
            lines.append(f"- {item}")
    else:
        lines.append("- orchestrator received a source-contract write-scope escalation that no active runtime role can currently satisfy")
    lines.extend(
        [
            "",
            "## Notes",
            "- generated from orchestrator inbox escalations requesting source-contract-capable maintenance",
            "- archive the triggering orchestrator escalation(s) only after this CEO turn is queued",
        ]
    )
    return "\n".join(lines) + "\n"


def _archive_orchestrator_escalation(repo_root: Path, message_path: Path) -> Path:
    processed_dir = repo_root / "runs" / "current" / "role-state" / "orchestrator" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    target = processed_dir / f"{message_path.stem}.escalated.md"
    message_path.replace(target)
    return target


def write_source_scope_notes(repo_root: Path, change_id: str) -> list[Path]:
    if role_pending(repo_root, "ceo"):
        return []

    created: list[Path] = []
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%d-%H%M%S")
    ceo_root = preferred_role_state_dir(repo_root, "ceo")
    inbox_dir = ceo_root / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    cutoff = now - RECOVERY_REQUEUE_COOLDOWN

    for index, escalation in enumerate(collect_source_scope_escalations(repo_root), start=1):
        archived_paths: list[Path] = []
        for message_path in escalation.message_paths:
            if message_path.exists():
                archived_paths.append(_archive_orchestrator_escalation(repo_root, message_path))
            else:
                archived_paths.append(
                    repo_root
                    / "runs"
                    / "current"
                    / "role-state"
                    / "orchestrator"
                    / "processed"
                    / f"{message_path.stem}.escalated.md"
                )
        archived_reads = [path.relative_to(repo_root).as_posix() for path in archived_paths]
        original_reads = {path.relative_to(repo_root).as_posix() for path in escalation.message_paths}
        escalation_for_note = SourceScopeEscalation(
            topic_slug=escalation.topic_slug,
            required_reads=tuple(
                _ordered_unique(
                    archived_reads
                    + [read for read in escalation.required_reads if read not in original_reads]
                )
            ),
            requested_paths=escalation.requested_paths,
            blocking_issues=escalation.blocking_issues,
            message_paths=tuple(archived_paths),
        )
        note_text = format_source_scope_note(repo_root, escalation_for_note, change_id)
        duplicate_recent_note = False
        for lane in ("inbox", "inflight", "processed"):
            lane_root = ceo_root / lane
            if not lane_root.exists():
                continue
            for existing_path in lane_root.glob(f"*-from-orchestrator-to-ceo-{escalation.topic_slug}.md"):
                existing_timestamp = note_timestamp(existing_path)
                if existing_timestamp is None or existing_timestamp < cutoff:
                    continue
                if existing_path.read_text(encoding="utf-8") == note_text:
                    duplicate_recent_note = True
                    break
            if duplicate_recent_note:
                break
        if duplicate_recent_note:
            continue

        suffix = "" if index == 1 else f"-{index}"
        note_path = inbox_dir / f"{stamp}-from-orchestrator-to-ceo-{escalation.topic_slug}{suffix}.md"
        note_path.write_text(note_text, encoding="utf-8")
        created.append(note_path)

    return created


def format_recovery_note(repo_root: Path, role: str, needs: list[ArtifactNeed], change_id: str) -> str:
    phase_labels = sorted({need.phase for need in needs}, key=lambda phase: PHASE_ORDER.get(phase, 99))
    required_reads: list[str] = ["runs/current/remarks.md"]

    for phase in phase_labels:
        required_reads.extend(PHASE_REQUIRED_READS.get(phase, ()))

    for need in needs:
        required_reads.extend(need.extra_reads)
        template_path = template_path_for_need(repo_root, need)
        if template_path is not None:
            required_reads.append(template_path.relative_to(repo_root).as_posix())
        required_reads.append(need.path.relative_to(repo_root).as_posix())

    seen_reads: set[str] = set()
    ordered_reads: list[str] = []
    for item in required_reads:
        if item not in seen_reads:
            seen_reads.add(item)
            ordered_reads.append(item)

    lines: list[str] = [
        "from: orchestrator",
        f"to: {ROLE_LABELS[role]}",
        "topic: recovery",
        f"purpose: {ROLE_PURPOSE[role]}",
        f"change_id: {change_id}",
        "",
        "## Required Reads",
    ]

    for item in ordered_reads:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Requested Outputs",
            "- create or replace the exact canonical artifact files listed below in your owned area",
            "- if the gate can advance after these artifacts are complete, emit the downstream handoff required for that next gate",
            "",
            "## Dependencies",
            "- none",
            "",
            "## Gate Status",
            "- blocked",
            "",
            "## Blocking Issues",
            "- completion is still blocked by unresolved canonical outputs or validation blockers in your owned area",
        ]
    )

    for need in needs:
        lines.append(f"- {need.reason}: {need.path.relative_to(repo_root).as_posix()}")

    lines.extend(
        [
            "",
            "## Notes",
            f"- recovery phases involved: {', '.join(phase_labels)}",
            "- do not replace the canonical filenames with semantically similar alternates",
            "- if another role must act next, issue an explicit inbox handoff instead of leaving the queue empty",
        ]
    )
    return "\n".join(lines) + "\n"


def _string_list(payload: dict[str, object], field: str) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _ordered_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def sync_change_role_load_for_recovery(
    repo_root: Path,
    change_id: str,
    role: str,
    needs: list[ArtifactNeed],
) -> None:
    if not change_id:
        return

    manifest_role = ROLE_LABELS.get(role, role)
    role_load_path = (
        repo_root
        / "runs"
        / "current"
        / "changes"
        / change_id
        / "role-loads"
        / f"{manifest_role}.yaml"
    )
    if not role_load_path.exists():
        return

    payload = yaml.safe_load(role_load_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return

    read_artifacts = _string_list(payload, "read_artifacts")
    write_artifacts = _string_list(payload, "write_artifacts")
    read_app_paths = _string_list(payload, "read_app_paths")
    write_app_paths = _string_list(payload, "write_app_paths")

    changed = False
    for need in needs:
        relative_path = need.path.relative_to(repo_root).as_posix()
        if relative_path.startswith("runs/current/artifacts/") or relative_path.startswith("runs/current/facts/"):
            new_read_artifacts = _ordered_unique(read_artifacts + [relative_path])
            new_write_artifacts = _ordered_unique(write_artifacts + [relative_path])
            changed = changed or new_read_artifacts != read_artifacts or new_write_artifacts != write_artifacts
            read_artifacts = new_read_artifacts
            write_artifacts = new_write_artifacts
            continue

        if relative_path.startswith("app/"):
            new_read_app_paths = _ordered_unique(read_app_paths + [relative_path])
            new_write_app_paths = _ordered_unique(write_app_paths + [relative_path])
            changed = changed or new_read_app_paths != read_app_paths or new_write_app_paths != write_app_paths
            read_app_paths = new_read_app_paths
            write_app_paths = new_write_app_paths

    if not changed:
        return

    payload["read_artifacts"] = read_artifacts
    payload["write_artifacts"] = write_artifacts
    payload["read_app_paths"] = read_app_paths
    payload["write_app_paths"] = write_app_paths
    role_load_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def write_recovery_notes(repo_root: Path, targets: dict[str, list[ArtifactNeed]], change_id: str) -> list[Path]:
    created: list[Path] = []
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%d-%H%M%S")
    for role, needs in sorted(targets.items()):
        sync_change_role_load_for_recovery(repo_root, change_id, role, needs)
        note_text = format_recovery_note(repo_root, role, needs, change_id)
        role_root = preferred_role_state_dir(repo_root, role)
        cutoff = now - RECOVERY_REQUEUE_COOLDOWN
        duplicate_recent_note = False
        for lane in ("inbox", "inflight", "processed"):
            lane_root = role_root / lane
            if not lane_root.exists():
                continue
            for existing_path in lane_root.glob(f"*-from-orchestrator-to-{role}-recovery.md"):
                existing_timestamp = note_timestamp(existing_path)
                if existing_timestamp is None or existing_timestamp < cutoff:
                    continue
                if existing_path.read_text(encoding="utf-8") == note_text:
                    duplicate_recent_note = True
                    break
            if duplicate_recent_note:
                break
        if duplicate_recent_note:
            continue

        inbox_dir = preferred_role_state_dir(repo_root, role) / "inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        note_path = inbox_dir / f"{stamp}-from-orchestrator-to-{role}-recovery.md"
        note_path.write_text(note_text, encoding="utf-8")
        created.append(note_path)
    return created


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--change-id", default="")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    targets = select_recovery_targets(repo_root)
    created = write_recovery_notes(repo_root, targets, args.change_id)
    created.extend(write_source_scope_notes(repo_root, args.change_id))
    for path in created:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
