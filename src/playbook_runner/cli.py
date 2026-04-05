from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .config import RunnerConfig
from .delivery_validation import validate_delivery
from .paths import PlaybookPaths


VALID_MODES = {"new", "iterate", "hotfix"}
VALID_SCOPES = {"fullstack", "frontend-only", "backend-only", "rules-only", "devops-only"}
VALID_ROLES = {"product_manager", "architect", "frontend", "backend", "qa", "deployment", "ceo"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_playbook")
    parser.add_argument("input_file", nargs="?", type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--mode", default="new", choices=sorted(VALID_MODES))
    parser.add_argument("--scope", default="fullstack", choices=sorted(VALID_SCOPES))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--role", choices=sorted(VALID_ROLES))
    parser.add_argument("--yolo", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--ceo-delivery-validate", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    if args.ceo_delivery_validate:
        if args.resume or args.role or args.input_file is not None:
            parser.error("--ceo-delivery-validate does not accept resume, role, or input arguments")
        paths = PlaybookPaths(repo_root)
        code, detail = validate_delivery(paths)
        if detail:
            print(detail, file=sys.stderr if code else sys.stdout)
        return code

    if args.resume and args.input_file is not None:
        parser.error("--resume does not accept an input file")
    if not args.resume:
        if args.input_file is None:
            parser.error("input_file is required unless --resume is set")
        if args.input_file.suffix != ".md":
            parser.error("input_file must be a .md file")

    config = RunnerConfig.from_env(repo_root)
    from .orchestrator import Orchestrator, RunRequest

    request = RunRequest(
        mode=args.mode,
        scope=args.scope,
        resume=args.resume,
        target_role=args.role,
        input_file=args.input_file.resolve() if args.input_file else None,
        yolo=args.yolo,
        verbose=args.verbose,
    )
    python_bin = sys.executable or "python3"
    runner = Orchestrator(config, request, python_bin=python_bin)
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())
