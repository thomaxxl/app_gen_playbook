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

from contracts.load_context import normalized_repo_root
from contracts.models import PolicyError
from contracts.sdlc_models import compile_sdlc_registry


RUN_MODE_ALIASES = {
    "new": "new-full-run",
    "new-full-run": "new-full-run",
    "iterate": "iterative-change-run",
    "iterative-change-run": "iterative-change-run",
    "hotfix": "app-only-hotfix",
    "app-only-hotfix": "app-only-hotfix",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_run_mode(run_mode: str) -> str:
    return RUN_MODE_ALIASES.get(run_mode.strip(), run_mode.strip())


def _load_runtime_extension(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PolicyError(f"expected mapping in runtime extension {path}")
    return payload


def resolve_plan(repo_root: Path, *, run_mode: str, overlays: list[str] | None = None) -> dict[str, Any]:
    registry = compile_sdlc_registry(repo_root, generated_at=utc_now())
    lifecycle_id = normalize_run_mode(run_mode)
    if lifecycle_id not in registry.lifecycles:
        raise PolicyError(f"unknown SDLC lifecycle {lifecycle_id}")
    lifecycle = registry.lifecycles[lifecycle_id]
    selected_overlays = []
    for overlay_id in overlays or []:
        if overlay_id not in registry.overlays:
            raise PolicyError(f"unknown SDLC overlay {overlay_id}")
        if overlay_id not in (lifecycle.get("allowed_overlays") or []):
            raise PolicyError(f"overlay {overlay_id} is not allowed for lifecycle {lifecycle_id}")
        selected_overlays.append(dict(registry.overlays[overlay_id]))

    resolved_phases: list[dict[str, Any]] = []
    phase_map: dict[str, dict[str, Any]] = {}
    for phase_id in lifecycle.get("phases", []):
        phase_payload = json.loads(json.dumps(registry.phases[phase_id]))
        phase_map[phase_id] = phase_payload
        resolved_phases.append(phase_payload)

    runtime_extensions: list[dict[str, Any]] = []
    for pattern in lifecycle.get("runtime_extension_paths", []) or []:
        for path in sorted(repo_root.glob(pattern)):
            extension = _load_runtime_extension(path)
            phase_id = str(extension.get("phase", ""))
            if phase_id not in phase_map:
                raise PolicyError(f"runtime extension {path} references unknown phase {phase_id}")
            insert_steps = extension.get("insert_steps") or []
            if not isinstance(insert_steps, list):
                raise PolicyError(f"runtime extension {path} has non-list insert_steps")
            phase_map[phase_id].setdefault("steps", []).extend(insert_steps)
            runtime_extensions.append(
                {
                    "id": str(extension.get("id", path.stem)),
                    "path": path.relative_to(repo_root).as_posix(),
                    "phase": phase_id,
                    "inserted_step_ids": [str(step.get("id", "")) for step in insert_steps],
                }
            )

    plan = {
        "generated_at": registry.generated_at,
        "lifecycle_id": lifecycle_id,
        "run_mode": lifecycle.get("run_mode", lifecycle_id),
        "phase_order": [phase["id"] for phase in resolved_phases],
        "phases": resolved_phases,
        "milestones": [
            registry.milestones[milestone_id]
            for milestone_id in lifecycle.get("milestones", [])
            if milestone_id in registry.milestones
        ],
        "overlays": selected_overlays,
        "runtime_extensions": runtime_extensions,
        "legal_transitions": [
            {"from": resolved_phases[index]["id"], "to": resolved_phases[index + 1]["id"]}
            for index in range(len(resolved_phases) - 1)
        ],
    }
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve the active SDLC plan for a run mode.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--run-mode", required=True)
    parser.add_argument("--overlay", action="append", default=[])
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    try:
        plan = resolve_plan(repo_root, run_mode=args.run_mode, overlays=args.overlay)
    except PolicyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else repo_root / "runs" / "current" / "orchestrator" / "sdlc-plan.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(yaml.safe_dump(plan, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
