from __future__ import annotations

from pathlib import Path

from orchestrator_common import resolve_repo_root


ROLE_PROFILE_ALIASES = {
    "product_manager": "role-product-manager",
    "product-manager": "role-product-manager",
    "architect": "role-architect",
    "frontend": "role-frontend",
    "backend": "role-backend",
    "deployment": "role-devops",
    "devops": "role-devops",
    "qa": "role-qa",
    "ceo": "role-ceo",
}

RUN_MODE_PROFILE_ALIASES = {
    "new": "run-fresh",
    "new-full-run": "run-fresh",
    "fresh-run": "run-fresh",
    "fresh": "run-fresh",
    "iterate": "run-iterative-change",
    "iterative-change-run": "run-iterative-change",
    "iterative-change": "run-iterative-change",
    "hotfix": "run-hotfix",
    "app-only-hotfix": "run-hotfix",
}

GATE_PROFILE_ALIASES = {
    "quality": "gate-quality",
    "acceptance": "gate-acceptance",
    "delivery": "gate-delivery",
}


def normalized_repo_root(value: str | Path) -> Path:
    return resolve_repo_root(value)


def role_profile_id(role: str | None) -> str | None:
    if not role:
        return None
    return ROLE_PROFILE_ALIASES.get(role.strip(), role.strip())


def run_mode_profile_id(run_mode: str | None) -> str | None:
    if not run_mode:
        return None
    return RUN_MODE_PROFILE_ALIASES.get(run_mode.strip(), run_mode.strip())


def gate_profile_id(gate: str | None) -> str | None:
    if not gate:
        return None
    return GATE_PROFILE_ALIASES.get(gate.strip(), gate.strip())


def feature_profile_ids(features: list[str] | None) -> list[str]:
    if not features:
        return []
    return [feature if feature.startswith("feature-") else f"feature-{feature}" for feature in features]
