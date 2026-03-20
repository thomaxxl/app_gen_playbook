#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.load_context import normalized_repo_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and record an SDLC attestation artifact.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--file", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    source = Path(args.file)
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    schema = json.loads((repo_root / "specs" / "policy" / "schema" / "attestation.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "<root>"
        result = {"ok": False, "error": f"{location}: {first.message}"}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    dest_dir = repo_root / "runs" / "current" / "policy" / "attestations"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / source.name
    if source.resolve() != dest.resolve():
        shutil.copy2(source, dest)
    result = {"ok": True, "output": dest.relative_to(repo_root).as_posix()}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
