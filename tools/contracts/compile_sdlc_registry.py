#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.load_context import normalized_repo_root
from contracts.models import PolicyError
from contracts.sdlc_models import compile_sdlc_registry


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile SDLC catalogs into a normalized registry.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    try:
        registry = compile_sdlc_registry(repo_root, generated_at=utc_now())
    except PolicyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else repo_root / "specs" / "policy" / "compiled" / "sdlc-registry.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(registry.to_json(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "ok": True,
        "output": str(output_path.relative_to(repo_root) if output_path.is_relative_to(repo_root) else output_path),
        "lifecycle_count": len(registry.lifecycles),
        "phase_count": len(registry.phases),
        "milestone_count": len(registry.milestones),
        "overlay_count": len(registry.overlays),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
