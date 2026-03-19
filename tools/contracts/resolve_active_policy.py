#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.load_context import (
    feature_profile_ids,
    gate_profile_id,
    normalized_repo_root,
    role_profile_id,
    run_mode_profile_id,
)
from contracts.models import PolicyError, compile_registry


def profile_matches_context(requirement: dict[str, Any], *, phase: str | None, run_mode: str | None, gate: str | None, features: list[str]) -> bool:
    applies_when = requirement.get("applies_when") or {}
    phases = set(applies_when.get("phases") or [])
    run_modes = set(applies_when.get("run_modes") or [])
    gates = set(applies_when.get("gates") or [])
    features_any = set(applies_when.get("features_any") or [])
    if phases and (phase is None or phase not in phases):
        return False
    if run_modes and (run_mode is None or run_mode not in run_modes):
        return False
    if gates and (gate is None or gate not in gates):
        return False
    if features_any and not any(feature in features_any for feature in features):
        return False
    return True


def resolve_policy(
    repo_root: Path,
    *,
    role: str | None,
    phase: str | None,
    run_mode: str | None,
    gate: str | None,
    features: list[str] | None,
    profiles: list[str] | None,
) -> dict[str, Any]:
    registry = compile_registry(repo_root)
    requested_profiles: list[str] = []
    for candidate in (
        role_profile_id(role),
        phase,
        run_mode_profile_id(run_mode),
        gate_profile_id(gate),
    ):
        if candidate:
            requested_profiles.append(candidate)
    requested_profiles.extend(feature_profile_ids(features))
    requested_profiles.extend(profiles or [])

    active_profiles: list[str] = []
    seen_profiles: set[str] = set()

    def visit(profile_id: str) -> None:
        if profile_id in seen_profiles:
            return
        if profile_id not in registry.profiles:
            raise PolicyError(f"unknown active profile {profile_id}")
        seen_profiles.add(profile_id)
        for included in registry.profiles[profile_id].get("includes", []):
            visit(str(included))
        active_profiles.append(profile_id)

    for profile_id in requested_profiles:
        visit(profile_id)

    requirement_ids: set[str] = set()
    for profile_id in active_profiles:
        for requirement_id in registry.profiles[profile_id].get("requirement_ids", []):
            requirement = registry.requirements[str(requirement_id)]
            if profile_matches_context(
                requirement,
                phase=phase,
                run_mode=run_mode,
                gate=gate,
                features=features or [],
            ):
                requirement_ids.add(str(requirement_id))

    return {
        "role": role,
        "phase": phase,
        "run_mode": run_mode,
        "gate": gate,
        "features_enabled": features or [],
        "active_profiles": active_profiles,
        "active_requirement_ids": sorted(requirement_ids),
        "requirements": {requirement_id: registry.requirements[requirement_id] for requirement_id in sorted(requirement_ids)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve active policy profiles and requirements.")
    parser.add_argument("--repo-root", default=".", help="path to the playbook repo root")
    parser.add_argument("--role", help="runtime role or display role")
    parser.add_argument("--phase", help="phase id such as phase-7-product-acceptance")
    parser.add_argument("--run-mode", help="run mode such as new, iterate, or hotfix")
    parser.add_argument("--gate", help="gate name such as quality or acceptance")
    parser.add_argument("--feature", action="append", default=[], help="enabled feature id")
    parser.add_argument("--profile", action="append", default=[], help="explicit extra profile id")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of YAML")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    try:
        payload = resolve_policy(
            repo_root,
            role=args.role,
            phase=args.phase,
            run_mode=args.run_mode,
            gate=args.gate,
            features=args.feature,
            profiles=args.profile,
        )
    except PolicyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(yaml.safe_dump(payload, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
