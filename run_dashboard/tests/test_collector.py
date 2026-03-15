from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from run_dashboard.collector import collect_handoffs, normalize_role
from run_dashboard.markdown import parse_frontmatter, parse_handoff_message


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class MarkdownParsingTests(unittest.TestCase):
    def test_parse_frontmatter_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "artifact.md"
            write_file(
                path,
                "\n".join(
                    [
                        "---",
                        "owner: frontend",
                        "phase: phase-3-ux-and-interaction-design",
                        "status: ready-for-handoff",
                        "depends_on:",
                        "  - a.md",
                        "  - b.md",
                        "unresolved:",
                        "  - none",
                        "---",
                        "",
                        "# Title",
                    ]
                ),
            )
            parsed = parse_frontmatter(path)
            self.assertEqual(parsed["owner"], "frontend")
            self.assertEqual(parsed["depends_on"], ["a.md", "b.md"])

    def test_parse_handoff_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.md"
            write_file(
                path,
                "\n".join(
                    [
                        "from: architect",
                        "to: devops",
                        "topic: runtime-bom",
                        "",
                        "## Required Reads",
                        "- a.md",
                        "- b.md",
                        "",
                        "## Gate Status",
                        "- blocked",
                    ]
                ),
            )
            parsed = parse_handoff_message(path)
            self.assertEqual(parsed["from"], "architect")
            self.assertEqual(parsed["to"], "devops")
            self.assertEqual(parsed["required reads"], ["a.md", "b.md"])
            self.assertEqual(parsed["gate status"], "blocked")


class CollectorTests(unittest.TestCase):
    def test_collect_handoffs_normalizes_devops_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_file(
                root / "runs/current/role-state/devops/inbox/msg.md",
                "\n".join(
                    [
                        "from: architect",
                        "to: devops",
                        "",
                        "## Gate Status",
                        "- blocked",
                    ]
                ),
            )
            rows = collect_handoffs(root, "run-1")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["to_role_code"], "devops")
            self.assertEqual(rows[0]["message_state"], "inbox")

    def test_normalize_role(self) -> None:
        self.assertEqual(normalize_role("deployment"), "devops")
        self.assertEqual(normalize_role("devops"), "devops")
        self.assertEqual(normalize_role("backend"), "backend")


if __name__ == "__main__":
    unittest.main()
