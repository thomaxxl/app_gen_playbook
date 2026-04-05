#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from final_review_pack import compile_final_review_pack
from orchestrator_common import resolve_repo_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile the final no-code review pack.")
    parser.add_argument("--repo-root", default=".", help="Repository root (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    payload = compile_final_review_pack(repo_root)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Compiled final review pack under {payload['final_root']}")
        print(f"Copied {len(payload['copied_files'])} files and {len(payload['copied_images'])} screenshots.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
