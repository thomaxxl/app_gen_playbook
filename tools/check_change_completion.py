#!/usr/bin/env python3
from __future__ import annotations

import argparse

from check_completion import main as check_completion_main


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    _ = parser.parse_args()
    return check_completion_main()


if __name__ == "__main__":
    raise SystemExit(main())
