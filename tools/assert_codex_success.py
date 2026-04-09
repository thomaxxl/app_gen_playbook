from __future__ import annotations

import sys

from assert_agent_success import main as agent_main


def main(argv: list[str]) -> int:
    return agent_main(argv, prog_name="assert_codex_success.py")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
