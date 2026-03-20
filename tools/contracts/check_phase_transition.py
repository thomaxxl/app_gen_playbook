#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.evaluate_sdlc import compute_sdlc_state
from contracts.load_context import normalized_repo_root
from contracts.models import PolicyError


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail closed when an SDLC phase transition is illegal.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--run-mode", required=True)
    parser.add_argument("--from", dest="from_phase", required=True)
    parser.add_argument("--to", dest="to_phase", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    try:
        plan, state = compute_sdlc_state(repo_root, run_mode=args.run_mode, current_phase=args.from_phase)
    except PolicyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    legal = any(item["from"] == args.from_phase and item["to"] == args.to_phase for item in plan["legal_transitions"])
    issues: list[str] = []
    if not legal:
        issues.append(f"illegal transition from {args.from_phase} to {args.to_phase} for lifecycle {plan['lifecycle_id']}")
    phase_lookup = {phase["id"]: phase for phase in plan["phases"]}
    target = phase_lookup.get(args.to_phase)
    if target is None:
        issues.append(f"unknown target phase {args.to_phase}")
    else:
        for milestone_id in target.get("entry_milestones", []) or []:
            milestone_state = state["milestones"].get(milestone_id)
            if milestone_state is None or milestone_state["status"] != "achieved":
                issues.append(f"required entry milestone {milestone_id} is not achieved")

    payload = {"ok": not issues, "issues": issues}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
