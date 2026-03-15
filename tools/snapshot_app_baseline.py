#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from orchestrator_common import hash_file, resolve_repo_root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    app_root = repo_root / "app"
    payload: dict[str, str] = {}

    if app_root.exists():
        for path in sorted(app_root.rglob("*")):
            if path.is_file():
                payload[str(path.relative_to(repo_root).as_posix())] = hash_file(path)

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
