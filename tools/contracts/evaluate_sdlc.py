#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.evaluate_policy import evaluate_requirement
from contracts.load_context import ROLE_PROFILE_ALIASES, normalized_repo_root
from contracts.models import compile_registry
from contracts.resolve_active_policy import resolve_policy
from contracts.resolve_sdlc_plan import resolve_plan


STEP_STATUSES = {"pending", "ready", "in_progress", "blocked", "pass", "fail", "warning", "waived", "not_applicable", "superseded"}
PHASE_STATUSES = {"not_started", "active", "blocked", "complete", "reopened", "abandoned"}
MILESTONE_STATUSES = {"locked", "open", "achieved", "blocked", "failed"}
POLICY_RUN_MODE_ALIASES = {
    "new-full-run": "new",
    "iterative-change-run": "iterate",
    "app-only-hotfix": "hotfix",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _artifacts_exist(repo_root: Path, paths: list[str]) -> bool:
    return all((repo_root / path).exists() for path in paths)


def compute_sdlc_state(repo_root: Path, *, run_mode: str, current_phase: str | None = None, overlays: list[str] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = resolve_plan(repo_root, run_mode=run_mode, overlays=overlays)
    policy_registry = compile_registry(repo_root)
    state_steps: dict[str, dict[str, Any]] = {}
    requirement_cache: dict[tuple[str, str], dict[str, Any]] = {}

    for phase in plan["phases"]:
        phase_id = str(phase["id"])
        phase_owner = (phase.get("owners") or [None])[0]
        policy_role = phase_owner if phase_owner in ROLE_PROFILE_ALIASES else None
        policy_phase = phase_id if phase_id in policy_registry.profiles else None
        policy_run_mode = POLICY_RUN_MODE_ALIASES.get(run_mode, run_mode)
        payload = resolve_policy(
            repo_root,
            role=policy_role,
            phase=policy_phase,
            run_mode=policy_run_mode,
            gate="quality" if phase_id in {"phase-6-integration-review", "phase-8-qa-pre-delivery-validation"} else ("acceptance" if phase_id == "phase-7-product-acceptance" else None),
            features=[],
            profiles=[],
        )
        active_requirements = payload["requirements"]
        for step in phase.get("steps", []):
            step_id = str(step["id"])
            output_artifacts = list((step.get("outputs") or {}).get("artifacts") or [])
            output_evidence = list((step.get("evidence") or {}).get("required_files") or [])
            required_paths = output_artifacts or output_evidence
            status = "pending"
            details: list[str] = []
            if step.get("requiredness") == "advisory":
                status = "not_applicable"
            elif required_paths and not _artifacts_exist(repo_root, required_paths):
                status = "pending"
                details.append("required outputs missing")
            else:
                linked_requirement_ids = [requirement_id for requirement_id in step.get("requirements", []) if requirement_id in active_requirements]
                if linked_requirement_ids:
                    linked_results = []
                    for requirement_id in linked_requirement_ids:
                        cache_key = (phase_id, requirement_id)
                        if cache_key not in requirement_cache:
                            requirement_cache[cache_key] = evaluate_requirement(repo_root, active_requirements[requirement_id], registry=policy_registry)
                        linked_results.append(requirement_cache[cache_key])
                    if any(result["status"] == "fail" for result in linked_results):
                        status = "fail"
                        details.extend(result["summary"] for result in linked_results if result["status"] == "fail")
                    elif any(result["status"] == "warning" for result in linked_results):
                        status = "warning"
                    else:
                        status = "pass"
                else:
                    status = "pass"
            state_steps[step_id] = {
                "phase": phase_id,
                "owner": (step.get("owners") or [None])[0],
                "status": status,
                "evidence": required_paths,
                "details": details,
            }

    phase_states: dict[str, dict[str, Any]] = {}
    for phase in plan["phases"]:
        phase_id = str(phase["id"])
        step_ids = [str(step["id"]) for step in phase.get("steps", [])]
        statuses = [state_steps[step_id]["status"] for step_id in step_ids]
        if all(status == "pass" for status in statuses):
            phase_status = "complete"
        elif any(status == "fail" for status in statuses):
            phase_status = "blocked"
        elif current_phase and phase_id == current_phase:
            phase_status = "active"
        elif any(status in {"warning"} for status in statuses):
            phase_status = "active"
        else:
            phase_status = "not_started"
        phase_states[phase_id] = {
            "status": phase_status,
            "step_ids": step_ids,
            "required_outputs": phase.get("required_outputs", []),
        }

    milestone_states: dict[str, dict[str, Any]] = {}
    for milestone in plan["milestones"]:
        milestone_id = str(milestone["id"])
        step_ids = list((milestone.get("achieved_when") or {}).get("all_steps_pass") or [])
        required_outputs = list((milestone.get("achieved_when") or {}).get("required_outputs") or [])
        if all(state_steps[step_id]["status"] == "pass" for step_id in step_ids) and _artifacts_exist(repo_root, required_outputs):
            status = "achieved"
        elif any(state_steps[step_id]["status"] == "fail" for step_id in step_ids):
            status = "failed"
        elif any(state_steps[step_id]["status"] in {"warning", "pass"} for step_id in step_ids):
            status = "open"
        else:
            status = "locked"
        milestone_states[milestone_id] = {
            "status": status,
            "phase": milestone["phase"],
            "blocks_transition": milestone.get("blocks_transition", False),
        }

    state = {
        "generated_at": utc_now(),
        "run_mode": run_mode,
        "current_phase": current_phase or "",
        "steps": state_steps,
        "phases": phase_states,
        "milestones": milestone_states,
    }
    return plan, state


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate SDLC step, phase, and milestone state.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--run-mode", required=True)
    parser.add_argument("--current-phase")
    parser.add_argument("--overlay", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    plan, state = compute_sdlc_state(repo_root, run_mode=args.run_mode, current_phase=args.current_phase, overlays=args.overlay)
    validation_dir = repo_root / "runs" / "current" / "evidence" / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    orchestrator_dir = repo_root / "runs" / "current" / "orchestrator"
    orchestrator_dir.mkdir(parents=True, exist_ok=True)
    (validation_dir / "sdlc-report.json").write_text(json.dumps({"plan": plan, "state": state}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (orchestrator_dir / "sdlc-state.yaml").write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
    if args.json:
        print(json.dumps({"plan": plan, "state": state}, indent=2, sort_keys=True))
    else:
        print(yaml.safe_dump(state, sort_keys=False))
    blocking = [item for item in state["milestones"].values() if item["status"] == "failed" and item["blocks_transition"]]
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
