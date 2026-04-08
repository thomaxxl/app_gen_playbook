#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import yaml

from check_phase5_ready import collect_phase5_blockers
from check_completion import collect_blockers
from contracts.evaluate_sdlc import compute_sdlc_state
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
from validate_handoff_inputs import validate_message


PHASE_ORDER = {
    "phase-0-intake-and-framing": 0,
    "phase-1-product-definition": 1,
    "phase-2-architecture-contract": 2,
    "phase-3-ux-and-interaction-design": 3,
    "phase-4-backend-design-and-rules-mapping": 4,
    "phase-5-parallel-implementation": 5,
    "phase-6-integration-review": 6,
    "phase-7-product-acceptance": 7,
    "phase-8-qa-pre-delivery-validation": 8,
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
    "qa": "qa",
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
    "qa": (
        "restore progress by completing the final independent QA delivery "
        "review artifacts and explicit live/screenshot proof for the current scope"
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
    "ui-preview-scroll-validation-missing",
    "ui-preview-shell-continuity-missing",
    "ui-preview-signoff-missing",
    "ui-preview-review-conclusion-missing",
    "ui-preview-fallback-invalid",
    "backend-orm-safrs-audit-failed",
    "observer-runtime-audit-failed",
    "frontend-route-coverage",
    "preview-coverage",
    "integration-review-coverage",
    "acceptance-review-coverage",
    "qa-review-coverage",
    "final-review-pack-incomplete",
    "reference-alignment-missing",
    "reference-fidelity-review-incomplete",
    "acceptance-missing-reference-fidelity",
}
PHASE5_REQUIRED_READ_MARKERS = (
    "playbook/task-bundles/frontend-implementation.yaml",
    "playbook/task-bundles/backend-implementation.yaml",
    "playbook/task-bundles/change-frontend-implementation.yaml",
    "playbook/task-bundles/change-backend-implementation.yaml",
    "playbook/process/phases/phase-5-parallel-implementation.md",
    "playbook/process/phases/phase-i5-frontend-implementation-delta.md",
    "playbook/process/phases/phase-i5-backend-implementation-delta.md",
)
REQUIRED_EVIDENCE_NEEDS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "product_manager",
        "runs/current/evidence/final/review-index.md",
        "missing",
        (
            "playbook/task-bundles/acceptance-review.yaml",
            "playbook/process/phases/phase-7-product-acceptance.md",
            "tools/compile_final_review_pack.py",
        ),
    ),
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
RUNTIME_ENVIRONMENT_HINT_PATTERN = re.compile(
    r"(browser[- ]runtime|runtime[- ]failed|runtime/environment|environment blocker|environment recovery|"
    r"operator/environment|browser launch|chromium launch|playwright|preview[- ]capture|"
    r"runtime proof|phase6-recovery-still-blocked|phase-6.*runtime)",
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
    "phase-8-qa-pre-delivery-validation": (
        "playbook/task-bundles/qa-delivery-review.yaml",
        "playbook/process/phases/phase-8-qa-pre-delivery-validation.md",
        "playbook/process/read-sets/qa-core.md",
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


@dataclass(frozen=True)
class RuntimeEnvironmentEscalation:
    topic_slug: str
    required_reads: tuple[str, ...]
    blocking_issues: tuple[str, ...]
    message_paths: tuple[Path, ...]


@dataclass(frozen=True)
class PendingPhaseCeoReview:
    phase_id: str
    approval_path: str
    required_reads: tuple[str, ...]


@dataclass(frozen=True)
class StalledRunTriage:
    blocker_paths: tuple[str, ...]
    blocker_summaries: tuple[str, ...]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def compute_facts_fingerprint(repo_root: Path) -> str:
    facts_root = repo_root / "runs" / "current" / "facts"
    digest = hashlib.sha256()
    if not facts_root.exists():
        digest.update(b"no-facts")
        return digest.hexdigest()[:16]
    any_files = False
    for path in sorted(facts_root.glob("*.json")):
        any_files = True
        digest.update(path.relative_to(repo_root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    if not any_files:
        digest.update(b"empty-facts")
    return digest.hexdigest()[:16]


def blocker_fingerprint(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:16]


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


def all_worker_roles_quiescent(repo_root: Path) -> bool:
    for role in (*active_core_roles(), "deployment"):
        if role_pending(repo_root, role):
            return False
    return True


def pending_role_message_paths(repo_root: Path, role: str) -> list[Path]:
    paths: list[Path] = []
    for role_root in all_role_state_dirs(repo_root, role):
        for subdir in ("inbox", "inflight"):
            directory = role_root / subdir
            if directory.exists():
                paths.extend(sorted(directory.glob("*.md")))
    return paths


def message_requires_phase5_gate(role: str, message_path: Path) -> bool:
    if role == "deployment":
        return True
    if role not in {"frontend", "backend"}:
        return False

    message_text = message_path.read_text(encoding="utf-8")
    headers = parse_message_headers(message_text)
    topic = headers.get("topic", "").strip().lower()
    if "implementation" in topic:
        return True

    sections = parse_message_sections(message_text, headers=headers)
    required_reads = [
        item.lower()
        for item in sections.get("required reads", [])
        if isinstance(item, str)
    ]
    return any(marker in read for marker in PHASE5_REQUIRED_READ_MARKERS for read in required_reads)


def phase5_gated_pending_paths(repo_root: Path, role: str) -> list[Path]:
    pending_paths = pending_role_message_paths(repo_root, role)
    if not pending_paths or not collect_phase5_blockers(repo_root):
        return []
    gated_paths = [path for path in pending_paths if message_requires_phase5_gate(role, path)]
    if len(gated_paths) != len(pending_paths):
        return []
    return gated_paths


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
    if path.endswith("/candidate/artifacts/ux/reference-alignment.md"):
        return (
            "playbook/task-bundles/change-frontend-design.yaml",
            "playbook/process/phases/phase-I4-design-delta.md",
            "skills/mui-db-admin-ux/SKILL.md",
        )
    if path.endswith("/verification/reference-fidelity-review.md"):
        return (
            "playbook/task-bundles/change-integration-review.yaml",
            "playbook/process/phases/phase-I6-integration-and-regression-review.md",
        )
    if path.endswith("/artifacts/product/acceptance-review.md"):
        return (
            "playbook/task-bundles/change-acceptance.yaml",
            "playbook/process/phases/phase-I7-change-acceptance.md",
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
        if relative_path in {
            "app/BUSINESS_RULES.md",
            "app/docs/playbook-baseline/current/manifest.yaml",
        }:
            # App-local exports are optional delivery artifacts, not generic
            # playbook recovery targets.
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

    if phase == "phase-8-qa-pre-delivery-validation":
        phase6_needs = [need for need in all_needs if need.phase == "phase-6-integration-review"]
        phase7_needs = [need for need in all_needs if need.phase == "phase-7-product-acceptance"]
        if phase6_needs or phase7_needs:
            return False
        return frontend_backend_quiescent(repo_root) and other_core_roles_quiescent(repo_root, role)

    return False


def select_recovery_targets(repo_root: Path) -> dict[str, list[ArtifactNeed]]:
    if initial_input_pending(repo_root):
        return {}

    needs = collect_artifact_needs(repo_root)
    needs.extend(collect_completion_blocker_needs(repo_root))
    runtime_environment_recovery_needed = bool(collect_runtime_environment_escalations(repo_root))
    targets: dict[str, list[ArtifactNeed]] = {}

    for role in ROLE_LABELS:
        role_needs = [need for need in needs if need.role == role]
        if not role_needs:
            continue

        eligible = [need for need in role_needs if should_recover_phase(repo_root, need.phase, needs, role)]
        pending_phase5_paths = phase5_gated_pending_paths(repo_root, role)
        if role_pending(repo_root, role):
            if not pending_phase5_paths or not eligible or not all(need.phase in EARLY_PHASES for need in eligible):
                continue
        if role == "architect" and role_pending(repo_root, "deployment"):
            eligible = [need for need in eligible if need.path.name != "runtime-bom.md"]
        if role == "architect" and runtime_environment_recovery_needed:
            eligible = [
                need
                for need in eligible
                if not (
                    need.phase == "phase-6-integration-review"
                    and need.path.name == "integration-review.md"
                    and need.reason.startswith("status=blocked")
                )
            ]
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


def collect_runtime_environment_escalations(repo_root: Path) -> list[RuntimeEnvironmentEscalation]:
    inbox_dir = repo_root / "runs" / "current" / "role-state" / "orchestrator" / "inbox"
    if not inbox_dir.exists():
        return []

    matched_paths: list[Path] = []
    required_reads: list[str] = []
    blocking_issues: list[str] = []
    topic_slug = "runtime-environment-recovery"

    for message_path in sorted(inbox_dir.glob("*.md")):
        message_text = message_path.read_text(encoding="utf-8")
        headers = parse_message_headers(message_text)
        if headers.get("to", "").strip().lower() != "orchestrator":
            continue

        sections = parse_message_sections(message_text, headers=headers)
        required_reads_section = [
            item for item in sections.get("required reads", []) if isinstance(item, str)
        ]
        requested_outputs = [
            item for item in sections.get("requested outputs", []) if isinstance(item, str)
        ]
        runtime_context = [
            *requested_outputs,
            *required_reads_section,
            *[item for item in sections.get("notes", []) if isinstance(item, str)],
            *[item for item in sections.get("blocking issues", []) if isinstance(item, str)],
            *[item for item in sections.get("remaining blockers", []) if isinstance(item, str)],
            *[item for item in sections.get("recovery outcome", []) if isinstance(item, str)],
            *[item for item in sections.get("next routing need", []) if isinstance(item, str)],
            *[item for item in sections.get("current blocker", []) if isinstance(item, str)],
            *[item for item in sections.get("current state", []) if isinstance(item, str)],
            *[item for item in sections.get("status", []) if isinstance(item, str)],
            headers.get("topic", ""),
            headers.get("purpose", ""),
        ]
        if _source_scope_paths(requested_outputs):
            continue
        if not any(RUNTIME_ENVIRONMENT_HINT_PATTERN.search(line) for line in runtime_context if line):
            continue

        matched_paths.append(message_path)
        required_reads.extend(required_reads_section)
        required_reads.append(message_path.relative_to(repo_root).as_posix())
        blocking_issues.extend(
            item for item in sections.get("blocking issues", []) if isinstance(item, str)
        )
        blocking_issues.extend(
            item for item in sections.get("remaining blockers", []) if isinstance(item, str)
        )

    if not matched_paths:
        return []

    return [
        RuntimeEnvironmentEscalation(
            topic_slug=topic_slug,
            required_reads=tuple(
                _ordered_unique(
                    [
                        "runs/current/orchestrator/run-status.json",
                        "runs/current/evidence/orchestrator/logs/orchestrator.log",
                        *required_reads,
                    ]
                )
            ),
            blocking_issues=tuple(_ordered_unique(blocking_issues)),
            message_paths=tuple(matched_paths),
        )
    ]


def format_source_scope_note(
    repo_root: Path,
    escalation: SourceScopeEscalation,
    change_id: str,
    *,
    facts_fingerprint: str,
    blocker_key: str,
    fingerprint: str,
) -> str:
    required_reads = _ordered_unique(["runs/current/remarks.md", *escalation.required_reads, *escalation.requested_paths])

    lines: list[str] = [
        "from: orchestrator",
        "to: ceo",
        f"topic: {escalation.topic_slug}",
        "purpose: restore progress by resolving source-contract or playbook write-scope escalations that runtime roles cannot satisfy",
        f"change_id: {change_id}",
        f"blocker_key: {blocker_key}",
        f"blocker_fingerprint: {fingerprint}",
        f"facts_fingerprint: {facts_fingerprint}",
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


def _message_headers(path: Path) -> dict[str, str]:
    return parse_message_headers(path.read_text(encoding="utf-8"))


def _same_generated_note_exists(role_root: Path, topic_slug: str, fingerprint: str) -> bool:
    for lane in ("inbox", "inflight", "processed"):
        lane_root = role_root / lane
        if not lane_root.exists():
            continue
        for existing_path in lane_root.glob(f"*-from-orchestrator-to-*-{topic_slug}*.md"):
            headers = _message_headers(existing_path)
            if headers.get("blockerfingerprint", "").strip() == fingerprint:
                return True
    return False


def _supersede_stale_generated_notes(role_root: Path, topic_slug: str, fingerprint: str) -> None:
    processed_dir = role_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    for lane in ("inbox",):
        lane_root = role_root / lane
        if not lane_root.exists():
            continue
        for existing_path in lane_root.glob(f"*-from-orchestrator-to-*-{topic_slug}*.md"):
            headers = _message_headers(existing_path)
            if headers.get("blockerfingerprint", "").strip() == fingerprint:
                continue
            target = processed_dir / f"{existing_path.stem}.superseded.md"
            existing_path.replace(target)


def _write_generated_note_with_prevalidation(
    repo_root: Path,
    runtime_role: str,
    note_path: Path,
    note_text: str,
) -> tuple[Path | None, Path | None]:
    note_path.write_text(note_text, encoding="utf-8")
    report = validate_message(repo_root, runtime_role, note_path)
    if report["valid"]:
        return note_path, None

    processed_dir = preferred_role_state_dir(repo_root, runtime_role) / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    parked_path = processed_dir / f"{note_path.stem}.blocked-until-changed.md"
    blockers = [
        blocker.get("message", "")
        for blocker in report.get("blockers", [])
        if isinstance(blocker, dict)
    ]
    parked_text = (
        note_text.rstrip()
        + "\n\n## Validation Blockers\n"
        + ("\n".join(f"- {item}" for item in blockers) if blockers else "- generated recovery note is still invalid")
        + "\n"
    )
    note_path.unlink(missing_ok=True)
    parked_path.write_text(parked_text, encoding="utf-8")
    return None, parked_path


def write_source_scope_notes(repo_root: Path, change_id: str) -> list[Path]:
    if role_pending(repo_root, "ceo"):
        return []

    created: list[Path] = []
    ceo_root = preferred_role_state_dir(repo_root, "ceo")
    inbox_dir = ceo_root / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    facts_fingerprint = compute_facts_fingerprint(repo_root)

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
        blocker_key = f"source-scope:{escalation.topic_slug}"
        fingerprint = blocker_fingerprint(
            blocker_key,
            facts_fingerprint,
            *escalation_for_note.requested_paths,
            *escalation_for_note.blocking_issues,
        )
        if _same_generated_note_exists(ceo_root, escalation.topic_slug, fingerprint):
            continue
        _supersede_stale_generated_notes(ceo_root, escalation.topic_slug, fingerprint)

        note_text = format_source_scope_note(
            repo_root,
            escalation_for_note,
            change_id,
            facts_fingerprint=facts_fingerprint,
            blocker_key=blocker_key,
            fingerprint=fingerprint,
        )
        suffix = "" if index == 1 else f"-{index}"
        note_path = inbox_dir / f"{utc_stamp()}-from-orchestrator-to-ceo-{escalation.topic_slug}{suffix}.md"
        written_path, _parked = _write_generated_note_with_prevalidation(repo_root, "ceo", note_path, note_text)
        if written_path is not None:
            created.append(written_path)

    return created


def format_runtime_environment_note(
    repo_root: Path,
    escalation: RuntimeEnvironmentEscalation,
    change_id: str,
    *,
    facts_fingerprint: str,
    blocker_key: str,
    fingerprint: str,
) -> str:
    required_reads = _ordered_unique(["runs/current/remarks.md", *escalation.required_reads])
    lines: list[str] = [
        "from: orchestrator",
        "to: ceo",
        f"topic: {escalation.topic_slug}",
        "purpose: restore progress by deciding whether the remaining runtime or environment blocker is locally repairable or requires operator action",
        f"change_id: {change_id}",
        f"blocker_key: {blocker_key}",
        f"blocker_fingerprint: {fingerprint}",
        f"facts_fingerprint: {facts_fingerprint}",
        "",
        "## Required Reads",
    ]
    for item in required_reads:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Requested Outputs",
            "- determine whether the remaining blocked runtime or environment lane can be repaired locally by CEO or delegated back to a normal role with a concrete new action",
            "- if the blocker is not locally repairable, write `runs/current/orchestrator/operator-action-required.md` with the exact operator action instead of leaving the run blocked with an empty worker queue",
            "- do not requeue the same runtime or environment blocker back to Architect unchanged",
            "",
            "## Dependencies",
            "- CEO stall-intervention authority",
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
        lines.append("- orchestrator received runtime or environment escalation(s) that no active runtime role can currently clear")
    lines.extend(
        [
            "",
            "## Notes",
            "- generated from orchestrator inbox escalations requesting runtime or environment recovery routing",
            "- archive the triggering orchestrator escalation(s) only after this CEO turn is queued",
        ]
    )
    return "\n".join(lines) + "\n"


def write_runtime_environment_notes(repo_root: Path, change_id: str) -> list[Path]:
    if role_pending(repo_root, "ceo"):
        return []

    created: list[Path] = []
    ceo_root = preferred_role_state_dir(repo_root, "ceo")
    inbox_dir = ceo_root / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    facts_fingerprint = compute_facts_fingerprint(repo_root)

    for escalation in collect_runtime_environment_escalations(repo_root):
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
        escalation_for_note = RuntimeEnvironmentEscalation(
            topic_slug=escalation.topic_slug,
            required_reads=tuple(
                _ordered_unique(
                    archived_reads
                    + [read for read in escalation.required_reads if read not in original_reads]
                )
            ),
            blocking_issues=escalation.blocking_issues,
            message_paths=tuple(archived_paths),
        )
        blocker_key = f"runtime-environment:{escalation.topic_slug}"
        fingerprint = blocker_fingerprint(
            blocker_key,
            facts_fingerprint,
            *escalation_for_note.blocking_issues,
        )
        if _same_generated_note_exists(ceo_root, escalation.topic_slug, fingerprint):
            continue
        _supersede_stale_generated_notes(ceo_root, escalation.topic_slug, fingerprint)

        note_text = format_runtime_environment_note(
            repo_root,
            escalation_for_note,
            change_id,
            facts_fingerprint=facts_fingerprint,
            blocker_key=blocker_key,
            fingerprint=fingerprint,
        )
        note_path = inbox_dir / f"{utc_stamp()}-from-orchestrator-to-ceo-{escalation.topic_slug}.md"
        written_path, _parked = _write_generated_note_with_prevalidation(repo_root, "ceo", note_path, note_text)
        if written_path is not None:
            created.append(written_path)

    return created


def load_run_mode_and_phase(repo_root: Path) -> tuple[str, str]:
    run_status_path = repo_root / "runs" / "current" / "orchestrator" / "run-status.json"
    if not run_status_path.exists():
        return "", ""
    try:
        payload = json.loads(run_status_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "", ""
    if not isinstance(payload, dict):
        return "", ""
    run_mode = str(payload.get("mode", "")).strip()
    current_phase = str(payload.get("current_phase", "")).strip()
    return run_mode, current_phase


def phase_doc_read(repo_root: Path, phase_id: str) -> str | None:
    candidate = repo_root / "playbook" / "process" / "phases" / f"{phase_id}.md"
    if candidate.exists():
        return candidate.relative_to(repo_root).as_posix()
    return None


def collect_pending_phase_ceo_reviews(repo_root: Path) -> list[PendingPhaseCeoReview]:
    run_mode, current_phase = load_run_mode_and_phase(repo_root)
    if not run_mode or not current_phase:
        return []
    try:
        plan, state = compute_sdlc_state(repo_root, run_mode=run_mode, current_phase=current_phase)
    except Exception:
        return []

    phase_payload = next((phase for phase in plan["phases"] if str(phase["id"]) == current_phase), None)
    if phase_payload is None:
        return []

    pending_reviews: list[PendingPhaseCeoReview] = []
    non_ceo_step_ids = [
        str(step["id"])
        for step in phase_payload.get("steps", [])
        if "ceo" not in (step.get("owners") or []) and step.get("requiredness") != "advisory"
    ]
    if non_ceo_step_ids and not all(state["steps"].get(step_id, {}).get("status") == "pass" for step_id in non_ceo_step_ids):
        return []

    for step in phase_payload.get("steps", []):
        if "ceo" not in (step.get("owners") or []):
            continue
        step_id = str(step["id"])
        step_status = str(state["steps"].get(step_id, {}).get("status", "")).strip()
        if step_status == "pass":
            continue

        approval_candidates = list((step.get("outputs") or {}).get("artifacts") or [])
        approval_candidates.extend(list((step.get("evidence") or {}).get("required_files") or []))
        if not approval_candidates:
            continue
        approval_path = str(approval_candidates[0])
        required_reads = [
            "runs/current/orchestrator/run-status.json",
            "playbook/process/quality-gates.md",
        ]
        phase_doc = phase_doc_read(repo_root, current_phase)
        if phase_doc:
            required_reads.append(phase_doc)
        required_reads.extend(
            item for item in phase_payload.get("required_outputs", []) if isinstance(item, str) and item != approval_path
        )
        pending_reviews.append(
            PendingPhaseCeoReview(
                phase_id=current_phase,
                approval_path=approval_path,
                required_reads=tuple(_ordered_unique(required_reads)),
            )
        )

    return pending_reviews


def collect_stalled_run_triage(repo_root: Path) -> StalledRunTriage | None:
    if role_pending(repo_root, "ceo"):
        return None
    if initial_input_pending(repo_root):
        return None
    if not all_worker_roles_quiescent(repo_root):
        return None
    if (repo_root / "runs" / "current" / "orchestrator" / "operator-action-required.md").exists():
        return None

    blockers = collect_blockers(repo_root)
    if not blockers:
        return None

    blocker_paths = _ordered_unique(
        [
            str(blocker.get("path", "")).strip()
            for blocker in blockers
            if str(blocker.get("path", "")).strip()
        ]
    )
    blocker_summaries: list[str] = []
    for blocker in blockers[:12]:
        owner = str(blocker.get("owner", "")).strip() or "unknown"
        phase = str(blocker.get("phase", "")).strip() or "unknown-phase"
        reason = str(blocker.get("reason", "")).strip() or "completion blocker remains unresolved"
        path = str(blocker.get("path", "")).strip()
        summary = f"{owner} {phase}: {reason}"
        if path:
            summary += f" ({path})"
        blocker_summaries.append(summary)
    if len(blockers) > 12:
        blocker_summaries.append(f"{len(blockers) - 12} additional completion blockers omitted for brevity")

    return StalledRunTriage(
        blocker_paths=tuple(blocker_paths),
        blocker_summaries=tuple(blocker_summaries),
    )


def format_stalled_run_triage_note(
    triage: StalledRunTriage,
    change_id: str,
    *,
    facts_fingerprint: str,
    blocker_key: str,
    fingerprint: str,
) -> str:
    required_reads = _ordered_unique(
        [
            "runs/current/remarks.md",
            "runs/current/orchestrator/run-status.json",
            "runs/current/evidence/orchestrator/logs/orchestrator.log",
            *triage.blocker_paths,
        ]
    )
    lines: list[str] = [
        "from: orchestrator",
        "to: ceo",
        "topic: stalled-run-triage",
        "purpose: diagnose a blocked run with empty worker queues and unresolved completion blockers, then route the concrete next action",
        f"change_id: {change_id}",
        f"blocker_key: {blocker_key}",
        f"blocker_fingerprint: {fingerprint}",
        f"facts_fingerprint: {facts_fingerprint}",
        "",
        "## Required Reads",
    ]
    for item in required_reads:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Requested Outputs",
            "- determine why the remaining blockers did not reopen a normal owner lane",
            "- either queue the concrete owner recovery note(s), repair the blocked run-owned artifact(s) directly, or route the issue to operator action if no local repair path remains",
            "- do not leave the run blocked with an empty worker queue after this CEO triage turn",
            "",
            "## Dependencies",
            "- CEO stall-intervention authority",
            "",
            "## Gate Status",
            "- blocked",
            "",
            "## Blocking Issues",
            "- the run has unresolved completion blockers but no actionable worker inbox or inflight work remained",
        ]
    )
    for item in triage.blocker_summaries:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Notes",
            "- generated only as a last-resort safety net when normal recovery routing produced no actionable worker note",
            "- use this to unblock routing gaps; do not normalize CEO as the primary owner for ordinary phase work",
        ]
    )
    return "\n".join(lines) + "\n"


def write_stalled_run_triage_notes(repo_root: Path, change_id: str) -> list[Path]:
    triage = collect_stalled_run_triage(repo_root)
    if triage is None:
        return []

    ceo_root = preferred_role_state_dir(repo_root, "ceo")
    inbox_dir = ceo_root / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    facts_fingerprint = compute_facts_fingerprint(repo_root)
    blocker_key = "stalled-run-triage:" + "|".join(triage.blocker_paths or triage.blocker_summaries)
    fingerprint = blocker_fingerprint(blocker_key, facts_fingerprint)
    if _same_generated_note_exists(ceo_root, "stalled-run-triage", fingerprint):
        return []
    _supersede_stale_generated_notes(ceo_root, "stalled-run-triage", fingerprint)

    note_text = format_stalled_run_triage_note(
        triage,
        change_id,
        facts_fingerprint=facts_fingerprint,
        blocker_key=blocker_key,
        fingerprint=fingerprint,
    )
    note_path = inbox_dir / f"{utc_stamp()}-from-orchestrator-to-ceo-stalled-run-triage.md"
    written_path, _parked = _write_generated_note_with_prevalidation(repo_root, "ceo", note_path, note_text)
    return [written_path] if written_path is not None else []


def format_phase_ceo_review_note(
    review: PendingPhaseCeoReview,
    change_id: str,
    *,
    facts_fingerprint: str,
    blocker_key: str,
    fingerprint: str,
) -> str:
    lines: list[str] = [
        "from: orchestrator",
        "to: ceo",
        f"topic: phase-review-{review.phase_id}",
        "purpose: critically review the completed phase outputs across components and subsystems before phase exit",
        f"change_id: {change_id}",
        f"phase: {review.phase_id}",
        f"blocker_key: {blocker_key}",
        f"blocker_fingerprint: {fingerprint}",
        f"facts_fingerprint: {facts_fingerprint}",
        "",
        "## Required Reads",
    ]
    for item in review.required_reads:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Requested Outputs",
            f"- critically review the completed phase package for `{review.phase_id}` across the affected components and subsystems",
            "- explicitly review UX/UI quality, even when the phase is not primarily design-owned",
            f"- if the phase is acceptable, write `{review.approval_path}`",
            "- if design, UX/UI, integration, or subsystem issues remain, do not write the approval artifact; keep the phase blocked and issue explicit corrective handoffs",
            "",
            "## Dependencies",
            "- CEO critical phase review gate",
            "",
            "## Gate Status",
            "- blocked until CEO review approves this phase",
            "",
            "## Blocking Issues",
            "- the normal phase-owned outputs appear complete, but the phase cannot exit without CEO critical review approval",
            "",
            "## Notes",
            "- the approval artifact must include Review Summary, Component and Subsystem Review, UX/UI Review, and Decision sections",
            "- UX/UI review is mandatory even for backend- or QA-heavy phases",
        ]
    )
    return "\n".join(lines) + "\n"


def write_phase_ceo_review_notes(repo_root: Path, change_id: str) -> list[Path]:
    if role_pending(repo_root, "ceo"):
        return []

    created: list[Path] = []
    ceo_root = preferred_role_state_dir(repo_root, "ceo")
    inbox_dir = ceo_root / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    facts_fingerprint = compute_facts_fingerprint(repo_root)

    for review in collect_pending_phase_ceo_reviews(repo_root):
        topic_slug = f"phase-review-{review.phase_id}"
        blocker_key = f"phase-review:{review.phase_id}"
        fingerprint = blocker_fingerprint(
            blocker_key,
            facts_fingerprint,
            review.phase_id,
            review.approval_path,
        )
        if _same_generated_note_exists(ceo_root, topic_slug, fingerprint):
            continue
        _supersede_stale_generated_notes(ceo_root, topic_slug, fingerprint)

        note_text = format_phase_ceo_review_note(
            review,
            change_id,
            facts_fingerprint=facts_fingerprint,
            blocker_key=blocker_key,
            fingerprint=fingerprint,
        )
        note_path = inbox_dir / f"{utc_stamp()}-from-orchestrator-to-ceo-{topic_slug}.md"
        written_path, _parked = _write_generated_note_with_prevalidation(repo_root, "ceo", note_path, note_text)
        if written_path is not None:
            created.append(written_path)

    return created


def format_recovery_note(
    repo_root: Path,
    role: str,
    needs: list[ArtifactNeed],
    change_id: str,
    *,
    facts_fingerprint: str,
    blocker_key: str,
    fingerprint: str,
) -> str:
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
        f"blocker_key: {blocker_key}",
        f"blocker_fingerprint: {fingerprint}",
        f"facts_fingerprint: {facts_fingerprint}",
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
    facts_fingerprint = compute_facts_fingerprint(repo_root)
    for role, needs in sorted(targets.items()):
        sync_change_role_load_for_recovery(repo_root, change_id, role, needs)
        role_root = preferred_role_state_dir(repo_root, role)
        if any(need.phase in EARLY_PHASES for need in needs):
            processed_dir = role_root / "processed"
            processed_dir.mkdir(parents=True, exist_ok=True)
            for pending_path in phase5_gated_pending_paths(repo_root, role):
                target = processed_dir / f"{pending_path.stem}.superseded-phase5-gated.md"
                pending_path.replace(target)
        blocker_key = "recovery:" + "|".join(
            f"{need.phase}:{need.path.relative_to(repo_root).as_posix()}:{need.reason}"
            for need in sorted(needs, key=lambda item: (item.phase, item.path.as_posix(), item.reason))
        )
        fingerprint = blocker_fingerprint(blocker_key, facts_fingerprint)
        if _same_generated_note_exists(role_root, "recovery", fingerprint):
            continue
        _supersede_stale_generated_notes(role_root, "recovery", fingerprint)

        note_text = format_recovery_note(
            repo_root,
            role,
            needs,
            change_id,
            facts_fingerprint=facts_fingerprint,
            blocker_key=blocker_key,
            fingerprint=fingerprint,
        )

        inbox_dir = preferred_role_state_dir(repo_root, role) / "inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        note_path = inbox_dir / f"{utc_stamp()}-from-orchestrator-to-{role}-recovery.md"
        written_path, _parked = _write_generated_note_with_prevalidation(repo_root, role, note_path, note_text)
        if written_path is not None:
            created.append(written_path)
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
    created.extend(write_runtime_environment_notes(repo_root, args.change_id))
    created.extend(write_phase_ceo_review_notes(repo_root, args.change_id))
    if not created:
        created.extend(write_stalled_run_triage_notes(repo_root, args.change_id))
    for path in created:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
