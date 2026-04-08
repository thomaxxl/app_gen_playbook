#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from delivery_gate_common import delivery_approval_terminal, qa_delivery_review_terminal
from execution_scope import active_scope_context, active_scope_phases
from orchestrator_common import (
    CORE_DISPLAY_ROLES,
    DISPLAY_TO_RUNTIME,
    all_role_state_dirs,
    iter_required_artifact_templates,
    owner_for_run_artifact,
    parse_metadata_block,
    resolve_repo_root,
)
from check_backend_orm_safrs import audit_backend_orm_safrs
from check_backend_observer_runtime import audit_backend_observer_runtime
from final_review_pack import FINAL_REVIEW_INDEX, collect_final_review_pack_issues
from validators.coverage.common import collect_quality_gate_evidence_issues
from validators.coverage.validate_acceptance_review_coverage import collect_issues as collect_acceptance_review_coverage_issues
from validators.coverage.validate_frontend_route_coverage import collect_issues as collect_frontend_route_coverage_issues
from validators.coverage.validate_integration_review_coverage import collect_issues as collect_integration_review_coverage_issues
from validators.coverage.validate_preview_coverage import collect_issues as collect_preview_coverage_issues
from validators.coverage.validate_qa_review_coverage import collect_issues as collect_qa_review_coverage_issues


READY_ARTIFACT_STATUSES = {"ready-for-handoff", "approved"}
NON_FINAL_ARTIFACT_STATUSES = {"blocked", "draft", "in-progress", "interrupted", "superseded", "unknown"}
CORE_DEVOPS_ARTIFACTS = {"README.md", "execution-prereqs.md"}
REQUIRED_APP_OUTPUTS = (
    ("app/.gitignore", "deployment"),
    ("app/README.md", "architect"),
    ("app/install.sh", "deployment"),
    ("app/run.sh", "deployment"),
    ("app/reference/admin.yaml", "backend"),
    ("app/backend/requirements.txt", "backend"),
    ("app/backend/run.py", "backend"),
    ("app/frontend/package.json", "frontend"),
    ("app/frontend/vite.config.ts", "frontend"),
    ("app/rules/rules.py", "backend"),
)
REQUIRED_EVIDENCE_OUTPUTS = (
    ("runs/current/evidence/contract-samples.md", "architect", "phase-6-integration-review"),
    ("runs/current/evidence/frontend-usability.md", "architect", "phase-6-integration-review"),
    ("runs/current/evidence/frontend-browser-proof.md", "architect", "phase-6-integration-review"),
    ("runs/current/evidence/ui-previews/manifest.md", "architect", "phase-6-integration-review"),
    ("runs/current/evidence/quality/crud-matrix.md", "architect", "phase-6-integration-review"),
    ("runs/current/evidence/quality/data-sourcing-audit.md", "architect", "phase-6-integration-review"),
    ("runs/current/evidence/quality/seed-data-audit.md", "architect", "phase-6-integration-review"),
    ("runs/current/evidence/quality/ui-copy-audit.md", "architect", "phase-6-integration-review"),
    ("runs/current/evidence/quality/test-results.md", "architect", "phase-6-integration-review"),
    ("runs/current/evidence/quality/quality-summary.md", "architect", "phase-6-integration-review"),
    ("runs/current/evidence/quality/coverage-report.md", "architect", "phase-6-integration-review"),
    ("runs/current/evidence/quality/review-plan.json", "architect", "phase-6-integration-review"),
)
FRONTEND_APP_OUTPUTS = {
    "app/frontend/package.json",
    "app/frontend/vite.config.ts",
}
BACKEND_APP_OUTPUTS = {
    "app/reference/admin.yaml",
    "app/backend/requirements.txt",
    "app/backend/run.py",
    "app/rules/rules.py",
}
DEVOPS_APP_OUTPUTS = {
    "app/.gitignore",
    "app/install.sh",
    "app/run.sh",
}
FRONTEND_EVIDENCE_OUTPUTS = {
    "runs/current/evidence/frontend-usability.md",
    "runs/current/evidence/frontend-browser-proof.md",
    "runs/current/evidence/ui-previews/manifest.md",
}
EVIDENCE_PLACEHOLDER_MARKER = "starter_status: pending-review-evidence"


def _normalize_reference_fidelity_text(text: str) -> str:
    lowered = text.lower().replace("-", " ")
    return re.sub(r"\s+", " ", lowered).strip()


def acceptance_records_reference_fidelity(text: str) -> bool:
    normalized = _normalize_reference_fidelity_text(text)
    required_markers = (
        "this acceptance review explicitly records the reference fidelity decision for binding external ui references",
        "reference fidelity decision for binding external ui references: approved",
    )
    return all(marker in normalized for marker in required_markers)
UI_PREVIEW_CAPTURE_STATES = {"captured", "not-required", "environment-blocked", "runtime-failed"}
UI_PREVIEW_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")
MARKDOWN_CAPTURE_STATUS_PATTERN = re.compile(
    r"(?im)^(?:-\s*)?capture_status:\s*([a-z0-9_-]+)\s*$"
)
UI_PREVIEW_CONTENT_VALIDATION_PATTERN = re.compile(
    r"(?im)^(?:-\s*)?content_validation_status:\s*([a-z0-9_-]+)\s*$"
)
UI_PREVIEW_REVIEW_CONCLUSION_PATTERN = re.compile(
    r"(?im)^(?:-\s*)?review_conclusion:\s*(.+?)\s*$"
)
UI_PREVIEW_VALIDATION_PATTERNS = {
    "frontend": re.compile(r"(?im)^(?:-\s*)?frontend_validation:\s*([a-z0-9_-]+)\s*$"),
    "architect": re.compile(r"(?im)^(?:-\s*)?architect_validation:\s*([a-z0-9_-]+)\s*$"),
    "product_manager": re.compile(r"(?im)^(?:-\s*)?product_manager_validation:\s*([a-z0-9_-]+)\s*$"),
}
CONTRACT_SAMPLES_REQUIRED_PATTERNS = (
    (
        re.compile(r"(?im)^##\s+SAFRS resource coverage\s*$"),
        "contract samples must include a SAFRS resource coverage section",
    ),
    (
        re.compile(r"(?im)^##\s+Relationship coverage\s*$"),
        "contract samples must include a relationship coverage section",
    ),
    (
        re.compile(r"(?im)^##\s+Approved non-SAFRS exceptions\s*$"),
        "contract samples must include an approved non-SAFRS exceptions section",
    ),
    (
        re.compile(r"/jsonapi\.json", re.IGNORECASE),
        "contract samples must cite live /jsonapi.json discovery",
    ),
)


def metadata_status(path: Path) -> str:
    if not path.exists():
        return ""
    return str(parse_metadata_block(path).get("status", "")).strip().lower()


def active_role_queues_present(repo_root: Path) -> bool:
    for display_role in CORE_DISPLAY_ROLES:
        runtime_role = DISPLAY_TO_RUNTIME[display_role]
        role_root = repo_root / "runs" / "current" / "role-state" / runtime_role
        for lane in ("inbox", "inflight"):
            lane_root = role_root / lane
            if lane_root.exists() and any(lane_root.glob("*.md")):
                return True
    ceo_root = repo_root / "runs" / "current" / "role-state" / "ceo"
    for lane in ("inbox", "inflight"):
        lane_root = ceo_root / lane
        if lane_root.exists() and any(lane_root.glob("*.md")):
            return True
    if is_optional_devops_active(repo_root):
        for deployment_root in all_role_state_dirs(repo_root, "deployment"):
            for lane in ("inbox", "inflight"):
                lane_root = deployment_root / lane
                if lane_root.exists() and any(lane_root.glob("*.md")):
                    return True
    return False


def collect_run_status_issues(repo_root: Path) -> list[dict[str, str]]:
    path = repo_root / "runs" / "current" / "orchestrator" / "run-status.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [
            artifact_blocker(
                "invalid-run-status",
                path,
                repo_root,
                "run-status.json is not valid JSON",
            )
        ]

    status = str(payload.get("status", "")).strip().lower()
    if status != "interrupted":
        return []
    return [
        artifact_blocker(
            "run-status-interrupted",
            path,
            repo_root,
            "run-status.json still says interrupted; completion must fail closed until the run is resumed or explicitly completed",
        )
    ]


def change_promotion_terminal(repo_root: Path) -> bool:
    scope_context = active_scope_context(repo_root)
    run_mode = str(scope_context.get("run_mode", "")).strip()
    if run_mode not in {"iterative-change-run", "app-only-hotfix"}:
        return False
    change_root = scope_context.get("change_root")
    if not isinstance(change_root, Path):
        return False
    promotion_path = change_root / "promotion.yaml"
    if not promotion_path.exists():
        return False
    text = promotion_path.read_text(encoding="utf-8")
    match = re.search(r"^accepted_at:\s*['\"]?([^'\"]*)['\"]?\s*$", text, flags=re.MULTILINE)
    return bool(match and match.group(1).strip())


def active_change_external_reference_manifest(repo_root: Path) -> tuple[Path | None, dict[str, object]]:
    scope_context = active_scope_context(repo_root)
    change_root = scope_context.get("change_root")
    if not isinstance(change_root, Path):
        return None, {}
    manifest_path = change_root / "external-references" / "manifest.json"
    if not manifest_path.exists():
        return None, {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return manifest_path, {}
    return manifest_path, payload if isinstance(payload, dict) else {}


def browser_proof_environment_fallback_ready(repo_root: Path) -> bool:
    browser_proof = repo_root / "runs" / "current" / "evidence" / "frontend-browser-proof.md"
    if not browser_proof.exists():
        return False
    proof_text = browser_proof.read_text(encoding="utf-8")
    proof_status_match = MARKDOWN_CAPTURE_STATUS_PATTERN.search(proof_text)
    if proof_status_match is None or proof_status_match.group(1).strip().lower() != "environment-blocked":
        return False

    host_runtime = repo_root / "runs" / "current" / "evidence" / "host-runtime-verification.md"
    if not host_runtime.exists():
        return False
    host_text = host_runtime.read_text(encoding="utf-8")
    return "- frontend_bind: ok" in host_text


def integration_review_environment_fallback_ready(repo_root: Path, required_path: Path) -> bool:
    if required_path.as_posix() != (repo_root / "runs" / "current" / "artifacts" / "architecture" / "integration-review.md").as_posix():
        return False
    if not browser_proof_environment_fallback_ready(repo_root):
        return False
    text = required_path.read_text(encoding="utf-8").lower()
    return "browser-level" in text and "environment" in text and "blocked" in text


def required_run_artifact_paths(repo_root: Path) -> list[tuple[Path, dict[str, object]]]:
    required_paths: list[tuple[Path, dict[str, object]]] = []
    for artifact_dir, template_path in iter_required_artifact_templates(repo_root):
        required_paths.append((
            repo_root / "runs" / "current" / "artifacts" / artifact_dir / template_path.name,
            parse_metadata_block(template_path),
        ))
    return sorted(required_paths, key=lambda item: str(item[0]))


def artifact_blocker(kind: str, path: Path, repo_root: Path, reason: str, owner: str = "", phase: str = "") -> dict[str, str]:
    return {
        "kind": kind,
        "path": path.relative_to(repo_root).as_posix(),
        "owner": owner,
        "phase": phase,
        "reason": reason,
    }


def likely_alias_hint(repo_root: Path, required_path: Path) -> str:
    template_path = None
    for artifact_dir, current_template in iter_required_artifact_templates(repo_root):
        candidate = repo_root / "runs" / "current" / "artifacts" / artifact_dir / current_template.name
        if candidate == required_path:
            template_path = current_template
            break
    if template_path is None:
        return ""

    metadata = parse_metadata_block(template_path)
    aliases = metadata.get("aliases", [])
    if isinstance(aliases, str):
        aliases = [aliases]
    required_dir = required_path.parent
    for alias in aliases:
        alias_path = required_dir / str(alias)
        if alias_path.exists():
            return alias_path.relative_to(repo_root).as_posix()
    return ""


def is_optional_devops_active(repo_root: Path) -> bool:
    devops_artifacts_dir = repo_root / "runs" / "current" / "artifacts" / "devops"
    if any(path.name not in CORE_DEVOPS_ARTIFACTS for path in devops_artifacts_dir.glob("*.md")):
        return True

    for deployment_dir in all_role_state_dirs(repo_root, "deployment"):
        inbox_dir = deployment_dir / "inbox"
        inflight_dir = deployment_dir / "inflight"
        if (
            (inbox_dir.exists() and any(inbox_dir.iterdir()))
            or (inflight_dir.exists() and any(inflight_dir.iterdir()))
        ):
            return True
    return False


def architect_blocked_integration_work(repo_root: Path) -> list[str]:
    architect_root = repo_root / "runs" / "current" / "role-state" / "architect"
    flagged: list[str] = []
    for lane in ("inbox", "inflight"):
        for path in sorted((architect_root / lane).glob("*.md")):
            raw_text = path.read_text(encoding="utf-8")
            if re.search(r"(?im)^(from|sender):\s*orchestrator\s*$", raw_text):
                continue
            text = raw_text.lower()
            if "blocked" not in text:
                continue
            if not re.search(r"\b(integration|drift)\b", text + " " + path.name.lower()):
                continue
            flagged.append(path.relative_to(repo_root).as_posix())
    return flagged


def execution_prereqs_playwright_ok(repo_root: Path) -> bool:
    prereq_path = repo_root / "runs" / "current" / "artifacts" / "devops" / "execution-prereqs.md"
    if not prereq_path.exists():
        return False
    text = prereq_path.read_text(encoding="utf-8")
    return bool(
        re.search(
            r"(?im)^-\s*(?:\[[xX ]\]\s+)?`playwright_screenshot`:\s*`ok`\s*\(required\)\s*$",
            text,
        )
    )


def app_declares_ui_preview_capture(repo_root: Path) -> bool:
    package_json_path = repo_root / "app" / "frontend" / "package.json"
    if not package_json_path.exists():
        return False
    text = package_json_path.read_text(encoding="utf-8")
    return '"capture:ui-previews"' in text


def ui_preview_validation_value(text: str, role: str) -> str:
    pattern = UI_PREVIEW_VALIDATION_PATTERNS[role]
    match = pattern.search(text)
    if match is None:
        return ""
    return match.group(1).strip().lower()


def collect_blockers(repo_root: Path) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    delivery_terminal = delivery_approval_terminal(repo_root)
    change_terminal = change_promotion_terminal(repo_root)
    scope_context = active_scope_context(repo_root)
    active_phases = set(active_scope_phases(repo_root))
    active_roles = {
        str(role)
        for role in (
            scope_context.get("classification", {}).get("active_roles")
            or scope_context.get("config", {}).get("active_roles")
            or []
        )
        if str(role).strip()
    }
    frontend_active = "frontend" in active_roles or not active_roles
    backend_active = "backend" in active_roles or not active_roles
    devops_active = "devops" in active_roles or "deployment" in active_roles
    qa_phase_active = "phase-8-qa-pre-delivery-validation" in active_phases or "phase-8-qa-pre-delivery-validation" in str(
        scope_context.get("run_status", {}).get("current_phase", "")
    )

    blockers.extend(collect_run_status_issues(repo_root))

    acceptance_review = (
        repo_root / "runs" / "current" / "artifacts" / "product" / "acceptance-review.md"
    )
    if not acceptance_review.exists():
        blockers.append(
            artifact_blocker(
                "missing-acceptance-review",
                acceptance_review,
                repo_root,
                "missing product acceptance review artifact",
                owner="product_manager",
                phase="phase-7-product-acceptance",
            )
        )
    else:
        acceptance_status = parse_metadata_block(acceptance_review).get("status")
        if acceptance_status != "approved":
            blockers.append(
                artifact_blocker(
                    "acceptance-not-approved",
                    acceptance_review,
                    repo_root,
                    f"product acceptance gate has not passed: status={acceptance_status!r}",
                    owner="product_manager",
                    phase="phase-7-product-acceptance",
                )
            )
        else:
            for issue in collect_final_review_pack_issues(repo_root):
                blockers.append(
                    artifact_blocker(
                        "final-review-pack-incomplete",
                        repo_root / FINAL_REVIEW_INDEX,
                        repo_root,
                        issue,
                        owner="product_manager",
                        phase="phase-7-product-acceptance",
                    )
                )
            reference_manifest_path, reference_manifest = active_change_external_reference_manifest(repo_root)
            references = reference_manifest.get("references", []) if isinstance(reference_manifest, dict) else []
            has_binding_visual_reference = any(
                isinstance(entry, dict)
                and str(entry.get("category", "")).strip() == "visual-ui"
                and str(entry.get("fidelity", "")).strip() == "mimic-look-and-feel"
                for entry in references if isinstance(references, list)
            )
            if has_binding_visual_reference and isinstance(scope_context.get("change_root"), Path):
                change_root = scope_context["change_root"]
                reference_alignment = change_root / "candidate" / "artifacts" / "ux" / "reference-alignment.md"
                reference_fidelity_review = change_root / "verification" / "reference-fidelity-review.md"
                if not reference_alignment.exists():
                    blockers.append(
                        artifact_blocker(
                            "reference-alignment-missing",
                            reference_alignment,
                            repo_root,
                            "binding external UI reference is missing a reference-alignment plan",
                            owner="frontend",
                            phase="phase-5-parallel-implementation",
                        )
                    )
                if not reference_fidelity_review.exists():
                    blockers.append(
                        artifact_blocker(
                            "reference-fidelity-review-incomplete",
                            reference_fidelity_review,
                            repo_root,
                            "binding external UI reference is missing a QA reference-fidelity review",
                            owner="qa",
                            phase="phase-I6-integration-and-regression-review",
                        )
                    )
                else:
                    fidelity_status = str(parse_metadata_block(reference_fidelity_review).get("status", "")).strip().lower()
                    if fidelity_status not in {"approved", "ready-for-handoff"}:
                        blockers.append(
                            artifact_blocker(
                                "reference-fidelity-review-incomplete",
                                reference_fidelity_review,
                                repo_root,
                                f"binding external UI reference fidelity review is not approved: status={fidelity_status or 'missing'}",
                                owner="qa",
                                phase="phase-6-integration-review",
                            )
                        )
                acceptance_text = acceptance_review.read_text(encoding="utf-8")
                if not acceptance_records_reference_fidelity(acceptance_text):
                    blockers.append(
                        artifact_blocker(
                            "acceptance-missing-reference-fidelity",
                            acceptance_review,
                            repo_root,
                            "product acceptance review must explicitly record the reference-fidelity decision for binding external UI references",
                            owner="product_manager",
                            phase="phase-7-product-acceptance",
                        )
                    )

    # After terminal delivery approval, stale phase-5 through phase-8 coverage
    # policy debt must not reopen the completed run, but blocked quality-gate
    # evidence remains a terminal blocker.
    if delivery_terminal:
        for issue in collect_quality_gate_evidence_issues(repo_root):
            blockers.append(
                {
                    "kind": "quality-gate-evidence",
                    "path": issue["path"],
                    "owner": "architect",
                    "phase": "phase-6-integration-review",
                    "reason": issue["reason"],
                }
            )
    elif not change_terminal:
        if frontend_active:
            for issue in collect_frontend_route_coverage_issues(repo_root):
                blockers.append(
                    {
                        "kind": "frontend-route-coverage",
                        "path": issue["path"],
                        "owner": "frontend",
                        "phase": "phase-5-parallel-implementation",
                        "reason": issue["reason"],
                    }
                )

            for issue in collect_preview_coverage_issues(repo_root):
                blockers.append(
                    {
                        "kind": "preview-coverage",
                        "path": issue["path"],
                        "owner": "architect",
                        "phase": "phase-6-integration-review",
                        "reason": issue["reason"],
                    }
                )

        for issue in collect_integration_review_coverage_issues(repo_root):
            blockers.append(
                {
                    "kind": "integration-review-coverage",
                    "path": issue["path"],
                    "owner": "architect",
                    "phase": "phase-6-integration-review",
                    "reason": issue["reason"],
                }
            )

        for issue in collect_acceptance_review_coverage_issues(repo_root):
            blockers.append(
                {
                    "kind": "acceptance-review-coverage",
                    "path": issue["path"],
                    "owner": "product_manager",
                    "phase": "phase-7-product-acceptance",
                    "reason": issue["reason"],
                }
            )

        if frontend_active and qa_phase_active:
            for issue in collect_qa_review_coverage_issues(repo_root):
                blockers.append(
                    {
                        "kind": "qa-review-coverage",
                        "path": issue["path"],
                        "owner": "qa",
                        "phase": "phase-8-qa-pre-delivery-validation",
                        "reason": issue["reason"],
                    }
                )

    for required_path, template_meta in required_run_artifact_paths(repo_root):
        owner = str(template_meta.get("owner", "")).strip()
        phase = str(template_meta.get("phase", "")).strip()
        if not required_path.exists():
            blocker = artifact_blocker(
                "missing-required-artifact",
                required_path,
                repo_root,
                "missing required artifact",
                owner=owner,
                phase=phase,
            )
            alias_hint = likely_alias_hint(repo_root, required_path)
            if alias_hint:
                blocker["alias_hint"] = alias_hint
            blockers.append(blocker)
            continue

        status = str(parse_metadata_block(required_path).get("status", "")).strip() or "unknown"
        if status == "stub":
            continue
        if status in NON_FINAL_ARTIFACT_STATUSES and integration_review_environment_fallback_ready(repo_root, required_path):
            continue
        if status in NON_FINAL_ARTIFACT_STATUSES:
            blockers.append(
                artifact_blocker(
                    "required-artifact-not-final",
                    required_path,
                    repo_root,
                    f"required artifact is not in a terminal ready state: status={status!r}",
                    owner=owner,
                    phase=phase,
                )
            )

    for artifact_path in sorted((repo_root / "runs" / "current" / "artifacts").rglob("*.md")):
        if artifact_path.name == "README.md":
            continue
        metadata = parse_metadata_block(artifact_path)
        status = metadata.get("status")
        if status == "stub":
            blockers.append(
                artifact_blocker(
                    "stub-artifact",
                    artifact_path,
                    repo_root,
                    "required artifact is still stub",
                    owner=owner_for_run_artifact(repo_root, artifact_path) or "",
                    phase=str(metadata.get("phase", "")).strip(),
                )
            )

    for display_role in CORE_DISPLAY_ROLES:
        runtime_role = DISPLAY_TO_RUNTIME[display_role]
        inbox_dir = repo_root / "runs" / "current" / "role-state" / runtime_role / "inbox"
        inflight_dir = repo_root / "runs" / "current" / "role-state" / runtime_role / "inflight"
        if inbox_dir.exists():
            pending = sorted(path.name for path in inbox_dir.glob("*.md"))
            if pending:
                blockers.append(
                    {
                        "kind": "core-inbox-not-empty",
                        "path": inbox_dir.relative_to(repo_root).as_posix(),
                        "owner": runtime_role,
                        "phase": "",
                        "reason": f"core inbox not empty: {', '.join(pending)}",
                    }
                )
        if inflight_dir.exists():
            pending = sorted(path.name for path in inflight_dir.glob("*.md"))
            if pending:
                blockers.append(
                    {
                        "kind": "core-inflight-not-empty",
                        "path": inflight_dir.relative_to(repo_root).as_posix(),
                        "owner": runtime_role,
                        "phase": "",
                        "reason": f"core inflight not empty: {', '.join(pending)}",
                    }
                )

    blocked_integration = architect_blocked_integration_work(repo_root)
    for path in blocked_integration:
        blockers.append(
            {
                "kind": "architect-blocked-integration-work",
                "path": path,
                "owner": "architect",
                "phase": "phase-6-integration-review",
                "reason": "blocked architect integration/drift work still open",
            }
        )

    if is_optional_devops_active(repo_root):
        for deployment_root in all_role_state_dirs(repo_root, "deployment"):
            deployment_inbox = deployment_root / "inbox"
            deployment_inflight = deployment_root / "inflight"
            if deployment_inbox.exists():
                pending = sorted(path.name for path in deployment_inbox.glob("*.md"))
                if pending:
                    blockers.append(
                        {
                            "kind": "optional-deployment-inbox-not-empty",
                            "path": deployment_inbox.relative_to(repo_root).as_posix(),
                            "owner": "deployment",
                            "phase": "",
                            "reason": f"optional deployment inbox not empty: {', '.join(pending)}",
                        }
                    )
            if deployment_inflight.exists():
                pending = sorted(path.name for path in deployment_inflight.glob("*.md"))
                if pending:
                    blockers.append(
                        {
                            "kind": "optional-deployment-inflight-not-empty",
                            "path": deployment_inflight.relative_to(repo_root).as_posix(),
                            "owner": "deployment",
                            "phase": "",
                            "reason": f"optional deployment inflight not empty: {', '.join(pending)}",
                        }
                    )

        verification_file = (
            repo_root / "runs" / "current" / "artifacts" / "devops" / "verification.md"
        )
        if not verification_file.exists():
            blockers.append(
                artifact_blocker(
                    "missing-optional-devops-verification",
                    verification_file,
                    repo_root,
                    "optional devops verification artifact is missing",
                    owner="deployment",
                    phase="deployment",
                )
            )

    for relative_path, owner in REQUIRED_APP_OUTPUTS:
        if relative_path in FRONTEND_APP_OUTPUTS and not frontend_active:
            continue
        if relative_path in BACKEND_APP_OUTPUTS and not backend_active:
            continue
        if relative_path in DEVOPS_APP_OUTPUTS and not devops_active:
            continue
        path = repo_root / relative_path
        if not path.exists():
            blockers.append(
                {
                    "kind": "missing-generated-app-output",
                    "path": relative_path,
                    "owner": owner,
                    "phase": "phase-5-parallel-implementation",
                    "reason": "required generated app output is missing",
                }
            )

    for relative_path, owner, phase in REQUIRED_EVIDENCE_OUTPUTS:
        if relative_path in FRONTEND_EVIDENCE_OUTPUTS and not frontend_active:
            continue
        path = repo_root / relative_path
        if not path.exists():
            blockers.append(
                {
                    "kind": "missing-required-evidence-output",
                    "path": relative_path,
                    "owner": owner,
                    "phase": phase,
                    "reason": "required evidence output is missing",
                }
            )
            continue
        text = path.read_text(encoding="utf-8")
        if EVIDENCE_PLACEHOLDER_MARKER in text:
            blockers.append(
                {
                    "kind": "required-evidence-output-placeholder",
                    "path": relative_path,
                    "owner": owner,
                    "phase": phase,
                    "reason": "required evidence output is still a starter placeholder",
                }
            )
            continue
        if relative_path == "runs/current/evidence/contract-samples.md":
            missing_requirements = [
                reason
                for pattern, reason in CONTRACT_SAMPLES_REQUIRED_PATTERNS
                if not pattern.search(text)
            ]
            if missing_requirements:
                blockers.append(
                    {
                        "kind": "contract-samples-unstructured",
                        "path": relative_path,
                        "owner": owner,
                        "phase": phase,
                        "reason": "; ".join(missing_requirements),
                    }
                )
                continue
        if relative_path == "runs/current/evidence/ui-previews/manifest.md":
            capture_state_match = MARKDOWN_CAPTURE_STATUS_PATTERN.search(text)
            capture_state = capture_state_match.group(1).strip().lower() if capture_state_match else ""
            if capture_state not in UI_PREVIEW_CAPTURE_STATES:
                blockers.append(
                    {
                        "kind": "ui-preview-manifest-unstructured",
                        "path": relative_path,
                        "owner": owner,
                        "phase": phase,
                        "reason": "ui preview manifest must declare capture_status as captured, not-required, environment-blocked, or runtime-failed",
                    }
                )
                continue
            if (
                capture_state == "environment-blocked"
                and execution_prereqs_playwright_ok(repo_root)
                and app_declares_ui_preview_capture(repo_root)
            ):
                blockers.append(
                    {
                        "kind": "ui-preview-fallback-invalid",
                        "path": relative_path,
                        "owner": owner,
                        "phase": phase,
                        "reason": "ui preview manifest claims environment-blocked even though execution prereqs prove Playwright capture is available and the app exposes capture:ui-previews",
                    }
                )
                continue
            if capture_state == "runtime-failed":
                blockers.append(
                    {
                        "kind": "ui-preview-runtime-failed",
                        "path": relative_path,
                        "owner": owner,
                        "phase": phase,
                        "reason": "ui preview manifest records runtime-failed; the canonical preview lane reached execution but still failed before producing reviewable output",
                    }
                )
                continue
            if capture_state == "captured":
                image_files = [
                    preview
                    for preview in path.parent.iterdir()
                    if preview.is_file() and preview.suffix.lower() in UI_PREVIEW_IMAGE_SUFFIXES
                ]
                if not image_files:
                    blockers.append(
                        {
                            "kind": "ui-preview-images-missing",
                            "path": relative_path,
                            "owner": owner,
                            "phase": phase,
                            "reason": "ui preview manifest says screenshots were captured, but no reviewable image files exist",
                        }
                    )
                    continue

                content_validation_match = UI_PREVIEW_CONTENT_VALIDATION_PATTERN.search(text)
                content_validation_status = (
                    content_validation_match.group(1).strip().lower()
                    if content_validation_match
                    else ""
                )
                if content_validation_status != "reviewed":
                    blockers.append(
                        {
                            "kind": "ui-preview-content-validation-missing",
                            "path": relative_path,
                            "owner": owner,
                            "phase": phase,
                            "reason": "captured ui preview manifest must declare content_validation_status: reviewed",
                        }
                    )

                normalized_text = text.lower()
                if "scroll_state_validation: reviewed" not in normalized_text:
                    blockers.append(
                        {
                            "kind": "ui-preview-scroll-validation-missing",
                            "path": relative_path,
                            "owner": owner,
                            "phase": phase,
                            "reason": "captured ui preview manifest must declare scroll_state_validation: reviewed",
                        }
                    )

                if "shell_continuity_validation: approved" not in normalized_text:
                    blockers.append(
                        {
                            "kind": "ui-preview-shell-continuity-missing",
                            "path": relative_path,
                            "owner": owner,
                            "phase": phase,
                            "reason": "captured ui preview manifest must declare shell_continuity_validation: approved",
                        }
                    )

                if "control_interactivity_validation: approved" not in normalized_text:
                    blockers.append(
                        {
                            "kind": "ui-preview-control-interactivity-missing",
                            "path": relative_path,
                            "owner": owner,
                            "phase": phase,
                            "reason": "captured ui preview manifest must declare control_interactivity_validation: approved",
                        }
                    )

                if "layout_density_validation: approved" not in normalized_text:
                    blockers.append(
                        {
                            "kind": "ui-preview-layout-density-missing",
                            "path": relative_path,
                            "owner": owner,
                            "phase": phase,
                            "reason": "captured ui preview manifest must declare layout_density_validation: approved",
                        }
                    )

                missing_validations = [
                    role.replace("_", "-")
                    for role in ("frontend", "architect", "product_manager")
                    if ui_preview_validation_value(text, role) != "approved"
                ]
                if missing_validations:
                    blockers.append(
                        {
                            "kind": "ui-preview-signoff-missing",
                            "path": relative_path,
                            "owner": owner,
                            "phase": phase,
                            "reason": "captured ui preview manifest is missing approved screenshot validation from: "
                            + ", ".join(missing_validations),
                        }
                    )

                review_conclusion_match = UI_PREVIEW_REVIEW_CONCLUSION_PATTERN.search(text)
                review_conclusion = (
                    review_conclusion_match.group(1).strip()
                    if review_conclusion_match
                    else ""
                )
                if not review_conclusion or "pending" in review_conclusion.lower():
                    blockers.append(
                        {
                            "kind": "ui-preview-review-conclusion-missing",
                            "path": relative_path,
                            "owner": owner,
                            "phase": phase,
                            "reason": "captured ui preview manifest must include a non-placeholder review_conclusion describing what the screenshots prove",
                        }
                    )

    if backend_active:
        backend_audit_issues = audit_backend_orm_safrs(repo_root)
        for issue in backend_audit_issues:
            blockers.append(
                {
                    "kind": "backend-orm-safrs-audit-failed",
                    "path": "app/backend/src",
                    "owner": "backend",
                    "phase": "phase-6-integration-review",
                    "reason": issue,
                }
            )
        observer_runtime_issues = audit_backend_observer_runtime(repo_root)
        for issue in observer_runtime_issues:
            blockers.append(
                {
                    "kind": "observer-runtime-audit-failed",
                    "path": "app/backend/src",
                    "owner": "backend",
                    "phase": "phase-6-integration-review",
                    "reason": issue,
                }
            )

    return blockers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    blockers = collect_blockers(repo_root)

    if args.json:
        print(json.dumps({"complete": not blockers, "blockers": blockers}, indent=2, sort_keys=True))
        return 1 if blockers else 0

    if blockers:
        print("run is not complete:")
        for blocker in blockers:
            line = blocker["reason"]
            if blocker.get("owner"):
                line += f" [owner={blocker['owner']}]"
            if blocker.get("phase"):
                line += f" [phase={blocker['phase']}]"
            if blocker.get("alias_hint"):
                line += f" [likely_alias={blocker['alias_hint']}]"
            print(f"- {line}: {blocker['path']}")
        return 1

    print("run is complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
