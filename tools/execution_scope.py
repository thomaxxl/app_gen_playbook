from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from orchestrator_common import resolve_repo_root


DEFAULT_SCOPE_PROFILE = "fullstack"
EXECUTION_SCOPE_MANIFEST = "playbook/routing/execution-scopes.yaml"
FALLBACK_SCOPES = {
    "fullstack": {
        "active_roles": ["product_manager", "architect", "frontend", "backend", "qa", "devops"],
        "new-full-run": {
            "active_phases": [
                "phase-0-intake-and-framing",
                "phase-1-product-definition",
                "phase-2-architecture-contract",
                "phase-3-ux-and-interaction-design",
                "phase-4-backend-design-and-rules-mapping",
                "phase-5-frontend-implementation",
                "phase-5-backend-implementation",
                "phase-6-integration-review",
                "phase-7-product-acceptance",
                "phase-8-qa-pre-delivery-validation",
            ],
            "gate_profiles": {
                "quality": ["gate-quality"],
                "acceptance": ["gate-acceptance"],
                "delivery": ["gate-delivery"],
            },
        },
        "iterative-change-run": {
            "baseline_source": "accepted-artifacts",
            "active_phases": [
                "phase-I1-change-intake-and-triage",
                "phase-I2-product-and-scope-delta",
                "phase-I3-architecture-and-contract-delta",
                "phase-I4-design-delta",
                "phase-I5-implementation-delta",
                "phase-I6-integration-and-regression-review",
                "phase-I7-change-acceptance",
            ],
            "gate_profiles": {
                "quality": ["gate-quality"],
                "acceptance": ["gate-acceptance"],
                "delivery": ["gate-delivery"],
            },
        },
        "app-only-hotfix": {
            "baseline_source": "portable-baseline",
            "active_phases": [
                "phase-I1-change-intake-and-triage",
                "phase-I2-product-and-scope-delta",
                "phase-I3-architecture-and-contract-delta",
                "phase-I5-implementation-delta",
                "phase-I6-integration-and-regression-review",
                "phase-I7-change-acceptance",
            ],
            "gate_profiles": {
                "quality": ["gate-quality"],
                "acceptance": ["gate-acceptance"],
            },
        },
    }
}


def normalized_repo_root(value: str | Path) -> Path:
    return resolve_repo_root(value)


def load_execution_scopes(repo_root: Path) -> dict[str, Any]:
    manifest_path = repo_root / EXECUTION_SCOPE_MANIFEST
    if not manifest_path.exists():
        return dict(FALLBACK_SCOPES)
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"execution scope manifest must decode to a mapping: {manifest_path}")
    return payload


def available_scope_profiles(repo_root: Path) -> list[str]:
    return sorted(load_execution_scopes(repo_root).keys())


def normalize_scope_profile(scope_profile: str | None) -> str:
    candidate = (scope_profile or "").strip()
    return candidate or DEFAULT_SCOPE_PROFILE


def load_run_status(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "runs" / "current" / "orchestrator" / "run-status.json"
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def active_change_root(repo_root: Path) -> Path | None:
    run_status = load_run_status(repo_root)
    change_id = str(run_status.get("change_id", "")).strip()
    if not change_id:
        return None
    change_root = repo_root / "runs" / "current" / "changes" / change_id
    if not change_root.exists():
        return None
    return change_root


def load_change_classification(change_root: Path | None) -> dict[str, Any]:
    if change_root is None:
        return {}
    path = change_root / "classification.yaml"
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def resolve_scope_config(repo_root: Path, *, run_mode: str | None, scope_profile: str | None) -> dict[str, Any]:
    manifest = load_execution_scopes(repo_root)
    normalized_scope = normalize_scope_profile(scope_profile)
    payload = manifest.get(normalized_scope)
    if not isinstance(payload, dict):
        raise ValueError(f"unknown scope profile: {normalized_scope}")

    run_mode_key = (run_mode or "").strip()
    mode_payload = payload.get(run_mode_key)
    if isinstance(mode_payload, dict):
        config = dict(payload)
        config.update(mode_payload)
        return config
    return dict(payload)


def active_scope_context(repo_root: Path) -> dict[str, Any]:
    run_status = load_run_status(repo_root)
    change_root = active_change_root(repo_root)
    classification = load_change_classification(change_root)

    run_mode = str(run_status.get("mode", "")).strip() or str(classification.get("requested_mode", "")).strip()
    scope_profile = normalize_scope_profile(
        classification.get("scope_profile")
        or run_status.get("scope_profile")
    )
    config = resolve_scope_config(repo_root, run_mode=run_mode, scope_profile=scope_profile)
    return {
        "run_mode": run_mode,
        "scope_profile": scope_profile,
        "config": config,
        "run_status": run_status,
        "change_root": change_root,
        "classification": classification,
    }


def active_scope_roles(repo_root: Path) -> list[str]:
    context = active_scope_context(repo_root)
    roles = context["classification"].get("active_roles") or context["config"].get("active_roles") or []
    return [str(role) for role in roles if str(role).strip()]


def active_scope_phases(repo_root: Path) -> list[str]:
    context = active_scope_context(repo_root)
    phases = context["classification"].get("active_phases") or context["config"].get("active_phases") or []
    return [str(phase) for phase in phases if str(phase).strip()]


def active_scope_gate_profiles(
    repo_root: Path,
    gate: str | None,
    *,
    run_mode: str | None = None,
    scope_profile: str | None = None,
) -> list[str]:
    if not gate:
        return []
    normalized_gate = str(gate).strip()
    context = active_scope_context(repo_root)
    if scope_profile is not None:
        config = resolve_scope_config(
            repo_root,
            run_mode=run_mode or str(context.get("run_mode", "")).strip(),
            scope_profile=scope_profile,
        )
    else:
        config = context.get("config", {})
    classification_profiles = context["classification"].get("active_policy_profiles") if scope_profile is None else []
    if isinstance(classification_profiles, dict):
        selected = classification_profiles.get(normalized_gate, [])
        if isinstance(selected, str):
            return [selected]
        if isinstance(selected, list) and selected:
            return [str(profile) for profile in selected if str(profile).strip()]
    elif isinstance(classification_profiles, list) and classification_profiles:
        # Legacy change packets stored a flat list that represented the active
        # quality-gate profile set only. Do not let that quality override bleed
        # into acceptance or delivery evaluation.
        if normalized_gate == "quality":
            return [str(profile) for profile in classification_profiles if str(profile).strip()]
    gate_profiles = config.get("gate_profiles") or {}
    selected = gate_profiles.get(normalized_gate, [])
    if isinstance(selected, str):
        return [selected]
    if isinstance(selected, list):
        return [str(profile) for profile in selected if str(profile).strip()]
    return []
