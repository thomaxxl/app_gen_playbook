#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.load_context import normalized_repo_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a human-readable SDLC board from sdlc-state.yaml.")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    state_path = repo_root / "runs" / "current" / "orchestrator" / "sdlc-state.yaml"
    if not state_path.exists():
        print("error: missing runs/current/orchestrator/sdlc-state.yaml", file=sys.stderr)
        return 1
    state = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
    print("# SDLC Board")
    print()
    print(f"- run_mode: `{state.get('run_mode', '')}`")
    print(f"- current_phase: `{state.get('current_phase', '')}`")
    print()
    print("## Phases")
    for phase_id, phase in (state.get("phases") or {}).items():
        print(f"- `{phase_id}`: `{phase.get('status', '')}`")
    print()
    print("## Milestones")
    for milestone_id, milestone in (state.get("milestones") or {}).items():
        print(f"- `{milestone_id}`: `{milestone.get('status', '')}`")
    print()
    print("## Blocked Steps")
    for step_id, step in (state.get("steps") or {}).items():
        if step.get("status") == "fail":
            print(f"- `{step_id}`: {', '.join(step.get('details') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
