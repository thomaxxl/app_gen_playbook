#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from run_dashboard.db import default_db_url, ensure_database
else:
    from .db import default_db_url, ensure_database


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db-url",
        default=os.environ.get("RUN_DASHBOARD_DATABASE_URL", os.environ.get("DATABASE_URL", default_db_url(repo_root))),
    )
    args = parser.parse_args()

    ensure_database(args.db_url)
    print(args.db_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
