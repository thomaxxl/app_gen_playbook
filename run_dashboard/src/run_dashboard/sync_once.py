#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from run_dashboard.collector import collect_run_snapshot
    from run_dashboard.db import default_db_url, write_snapshot
else:
    from .collector import collect_run_snapshot
    from .db import default_db_url, write_snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--playbook-root", required=True)
    parser.add_argument("--project-slug", default="app_gen_playbook")
    parser.add_argument("--project-name", default="App Gen Playbook")
    repo_root = Path(__file__).resolve().parents[3]
    parser.add_argument(
        "--db-url",
        default=os.environ.get("RUN_DASHBOARD_DATABASE_URL", os.environ.get("DATABASE_URL", default_db_url(repo_root))),
    )
    parser.add_argument("--ensure-schema", action="store_true")
    parser.add_argument("--skip-db", action="store_true")
    parser.add_argument("--dump-json", action="store_true")
    args = parser.parse_args()

    playbook_root = Path(args.playbook_root).resolve()

    snapshot = collect_run_snapshot(playbook_root, args.project_slug, args.project_name)

    if args.dump_json:
        print(json.dumps(snapshot, indent=2, sort_keys=True))

    if not args.skip_db and snapshot.get("run"):
        write_snapshot(args.db_url, snapshot, ensure_schema=args.ensure_schema)
    elif not args.skip_db and args.ensure_schema:
        write_snapshot(args.db_url, snapshot, ensure_schema=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
