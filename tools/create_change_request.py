#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from orchestrator_common import resolve_repo_root


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--mode", required=True)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        raise SystemExit(f"error: input file not found: {input_path}")

    stamp = utc_stamp()
    change_id = f"CR-{stamp}"
    change_dir = repo_root / "runs" / "current" / "artifacts" / "product" / "changes" / change_id
    change_dir.mkdir(parents=True, exist_ok=True)
    (change_dir / "request.md").write_text(input_path.read_text(encoding="utf-8"), encoding="utf-8")

    topic = "change-request" if args.mode == "iterative-change-run" else "hotfix-request"
    inbox_name = f"{stamp}-from-operator-to-product_manager-{topic}.md"
    inbox_path = repo_root / "runs" / "current" / "role-state" / "product_manager" / "inbox" / inbox_name
    inbox_path.parent.mkdir(parents=True, exist_ok=True)
    inbox_path.write_text(
        "\n".join(
            [
                "from: operator",
                "to: product_manager",
                f"topic: {topic}",
                f"change_id: {change_id}",
                f"change_type: {args.mode}",
                "purpose: classify and route the requested app change",
                "",
                "## Required Reads",
                "- runs/current/input.md",
                f"- runs/current/artifacts/product/changes/{change_id}/request.md",
                "- runs/current/artifacts/product/",
                "",
                "## Requested Outputs",
                "- classify the request and select the proper run mode",
                "- update product delta artifacts as needed",
                "- hand off the impacted lanes",
                "",
                "## Dependencies",
                "- current accepted run artifacts",
                "- current app baseline",
                "",
                "## Gate Status",
                "- pass",
                "",
                "## Blocking Issues",
                "- none",
                "",
                "## Notes",
                "- generated automatically by the orchestrator for an existing-app change run",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(change_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
