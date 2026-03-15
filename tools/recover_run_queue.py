#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from orchestrator_common import (
    DISPLAY_TO_RUNTIME,
    CORE_DISPLAY_ROLES,
    RUN_ARTIFACT_TEMPLATE_DIRS,
    iter_required_artifact_templates,
    parse_metadata_block,
    resolve_repo_root,
)


PHASE_ORDER = {
    "phase-0-intake-and-framing": 0,
    "phase-1-product-definition": 1,
    "phase-2-architecture-contract": 2,
    "phase-3-ux-and-interaction-design": 3,
    "phase-4-backend-design-and-rules-mapping": 4,
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

ROLE_LABELS = {
    "product_manager": "product_manager",
    "architect": "architect",
    "frontend": "frontend",
    "backend": "backend",
    "deployment": "deployment",
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


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def active_core_roles() -> tuple[str, ...]:
    return tuple(DISPLAY_TO_RUNTIME[name] for name in CORE_DISPLAY_ROLES)


def role_pending(repo_root: Path, role: str) -> bool:
    role_root = repo_root / "runs" / "current" / "role-state" / role
    for subdir in ("inbox", "inflight"):
        directory = role_root / subdir
        if directory.exists() and any(directory.glob("*.md")):
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

        if run_path.name == "acceptance-review.md" and status != "approved":
            needs.append(ArtifactNeed(role=role, phase=phase, path=run_path, reason=f"status={status or 'missing-status'}"))

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
        return True

    early_needs = [need for need in all_needs if need.phase in EARLY_PHASES]
    if early_needs:
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
    needs = collect_artifact_needs(repo_root)
    targets: dict[str, list[ArtifactNeed]] = {}

    for role in ROLE_LABELS:
        if role_pending(repo_root, role):
            continue

        role_needs = [need for need in needs if need.role == role]
        if not role_needs:
            continue

        eligible = [need for need in role_needs if should_recover_phase(repo_root, need.phase, needs, role)]
        if not eligible:
            continue

        targets[role] = sorted(
            eligible,
            key=lambda need: (PHASE_ORDER.get(need.phase, 99), str(need.path)),
        )

    return targets


def format_recovery_note(repo_root: Path, role: str, needs: list[ArtifactNeed], change_id: str) -> str:
    phase_labels = sorted({need.phase for need in needs}, key=lambda phase: PHASE_ORDER.get(phase, 99))
    required_reads: list[str] = ["runs/current/remarks.md"]

    for phase in phase_labels:
        required_reads.extend(PHASE_REQUIRED_READS.get(phase, ()))

    for need in needs:
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
            "- completion is still blocked by missing or non-final canonical artifacts in your owned area",
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


def write_recovery_notes(repo_root: Path, targets: dict[str, list[ArtifactNeed]], change_id: str) -> list[Path]:
    created: list[Path] = []
    stamp = utc_stamp()
    for role, needs in sorted(targets.items()):
        inbox_dir = repo_root / "runs" / "current" / "role-state" / role / "inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        note_path = inbox_dir / f"{stamp}-from-orchestrator-to-{role}-recovery.md"
        note_path.write_text(format_recovery_note(repo_root, role, needs, change_id), encoding="utf-8")
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
    for path in created:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
