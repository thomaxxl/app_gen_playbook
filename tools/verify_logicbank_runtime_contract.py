#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _repo_root(value: str | None) -> Path:
    if value:
        return Path(value).resolve()
    return Path(__file__).resolve().parents[1]


def _backend_site_packages(repo_root: Path) -> Path:
    candidates = sorted((repo_root / "app" / "backend" / ".venv" / "lib").glob("python*/site-packages"))
    if not candidates:
        raise FileNotFoundError("backend runtime site-packages directory not found under app/backend/.venv/lib")
    return candidates[0]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _signature(source: str, name: str) -> str:
    match = re.search(
        rf"def\s+{re.escape(name)}\((.*?)\)\s*(?:->\s*([^:]+))?:",
        source,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError(f"could not find function signature for {name}")
    raw_args = match.group(1)
    raw_return = match.group(2)
    args = " ".join(part.strip() for part in raw_args.splitlines())
    args = re.sub(r"\s+", " ", args).strip()
    if raw_return:
        returned = " ".join(part.strip() for part in raw_return.splitlines())
        returned = re.sub(r"\s+", " ", returned).strip()
        return f"({args}) -> {returned}"
    return f"({args})"


def verify(repo_root: Path) -> dict[str, object]:
    site_packages = _backend_site_packages(repo_root)
    logicbank_root = site_packages / "logic_bank"
    init_path = logicbank_root / "__init__.py"
    logic_bank_source = _read(logicbank_root / "logic_bank.py")
    logic_row_source = _read(logicbank_root / "exec_row_logic" / "logic_row.py")
    row_event_source = _read(logicbank_root / "rule_type" / "row_event.py")
    listeners_source = _read(logicbank_root / "exec_trans_logic" / "listeners.py")

    return {
        "logicbank_module": str(init_path),
        "logicbank_activate_signature": _signature(logic_bank_source, "activate"),
        "logicrow_log_signature": _signature(logic_row_source, "log"),
        "logicrow_new_logic_row_signature": _signature(logic_row_source, "new_logic_row"),
        "event_callback_keywords_verified": "row=logic_row.row, old_row=logic_row.old_row, logic_row=logic_row" in row_event_source,
        "logic_row_log_usage_verified": "each_logic_row.log(" in listeners_source,
        "event_tokens_verified": {
            "early_row_event": "EarlyRowEvent" in row_event_source,
            "row_event": "RowEvent" in row_event_source,
            "commit_row_event": "CommitRowEvent" in row_event_source,
            "after_flush_row_event": "AfterFlushRowEvent" in row_event_source,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the installed LogicBank runtime contract.")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = _repo_root(args.repo_root)
    payload = verify(repo_root)

    required_truthy = {
        "event_callback_keywords_verified": payload.get("event_callback_keywords_verified"),
        "logic_row_log_usage_verified": payload.get("logic_row_log_usage_verified"),
    }
    required_truthy.update(payload.get("event_tokens_verified", {}))
    failures = [name for name, ok in required_truthy.items() if not ok]

    if args.json:
        print(json.dumps({
            "ok": not failures,
            "payload": payload,
            "failures": failures,
        }, indent=2))
    else:
        print("LogicBank runtime verification")
        print(f"- module: {payload['logicbank_module']}")
        print(f"- LogicBank.activate: {payload['logicbank_activate_signature']}")
        print(f"- LogicRow.log: {payload['logicrow_log_signature']}")
        print(f"- LogicRow.new_logic_row: {payload['logicrow_new_logic_row_signature']}")
        print(f"- verified callback/event notes: {'ok' if not failures else ', '.join(failures)}")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
