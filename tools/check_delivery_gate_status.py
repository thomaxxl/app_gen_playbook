#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from delivery_gate_common import delivery_approval_recorded, delivery_approval_terminal, qa_delivery_review_terminal


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--qa-terminal", action="store_true")
    parser.add_argument("--delivery-recorded", action="store_true")
    parser.add_argument("--delivery-terminal", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    payload = {
        "qa_terminal": qa_delivery_review_terminal(repo_root),
        "delivery_recorded": delivery_approval_recorded(repo_root),
        "delivery_terminal": delivery_approval_terminal(repo_root),
    }

    selected_checks = []
    if args.qa_terminal:
        selected_checks.append(payload["qa_terminal"])
    if args.delivery_recorded:
        selected_checks.append(payload["delivery_recorded"])
    if args.delivery_terminal:
        selected_checks.append(payload["delivery_terminal"])

    ok = all(selected_checks) if selected_checks else payload["delivery_terminal"]
    payload["ok"] = ok

    if args.json or not selected_checks:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
