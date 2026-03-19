#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.load_context import normalized_repo_root
from contracts.models import PolicyError, compile_registry, write_compiled_registry


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile sidecar policy requirements into a normalized registry.")
    parser.add_argument("--repo-root", default=".", help="path to the playbook repo root")
    parser.add_argument("--output", help="optional output path for compiled registry JSON")
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    try:
        registry = compile_registry(repo_root)
    except PolicyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output_path = write_compiled_registry(repo_root, registry, Path(args.output) if args.output else None)
    summary = {
        "ok": True,
        "output": display_path(output_path, repo_root),
        "requirement_count": len(registry.requirements),
        "profile_count": len(registry.profiles),
        "requirement_set_count": len(registry.requirement_sets),
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"compiled {summary['requirement_count']} requirements into {summary['output']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
