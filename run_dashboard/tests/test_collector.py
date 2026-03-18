from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from run_dashboard.collector import collect_artifacts, collect_handoffs, collect_run_files, normalize_role
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
            run_files, _, _ = collect_run_files(root, "run-1")
            rows, relationships = collect_handoffs(root, "run-1", run_files)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["to_role_code"], "devops")
            self.assertEqual(rows[0]["message_state"], "inbox")
            self.assertEqual(rows[0]["path"], "runs/current/role-state/devops/inbox/msg.md")
            self.assertTrue(any(rel["relation_type"] == "blocking_issue_ref" for rel in relationships) is False)

    def test_collect_handoffs_preserves_duplicate_states_by_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "\n".join(
                [
                    "from: architect",
                    "to: backend",
                ]
            )
            write_file(root / "runs/current/role-state/backend/inbox/msg.md", content)
            write_file(root / "runs/current/role-state/backend/processed/msg.md", content)
            run_files, _, _ = collect_run_files(root, "run-1")
            rows, _ = collect_handoffs(root, "run-1", run_files)
            self.assertEqual(len(rows), 2)
            self.assertEqual({row["state_dir"] for row in rows}, {"inbox", "processed"})
            self.assertEqual(len({row["id"] for row in rows}), 2)

    def test_collect_artifacts_recurses_into_family_subdirectories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_file(
                root / "runs/current/artifacts/ux/nested/navigation.md",
                "\n".join(
                    [
                        "---",
                        "owner: frontend",
                        "phase: phase-3-ux-and-interaction-design",
                        "status: ready-for-handoff",
                        "---",
                        "",
                        "# Navigation",
                    ]
                ),
            )
            run_files, markdown_documents, _ = collect_run_files(root, "run-1")
            packages, artifacts, dependencies, relationships = collect_artifacts(root, "run-1", run_files, markdown_documents)
            self.assertEqual(len(packages), 1)
            self.assertEqual(packages[0]["family"], "ux")
            self.assertEqual(packages[0]["overall_status"], "ready_for_handoff")
            self.assertEqual(len(artifacts), 1)
            self.assertTrue(artifacts[0]["path"].endswith("runs/current/artifacts/ux/nested/navigation.md"))
            self.assertEqual(dependencies, [])
            self.assertEqual(relationships, [])

    def test_normalize_role(self) -> None:
        self.assertEqual(normalize_role("deployment"), "devops")
        self.assertEqual(normalize_role("devops"), "devops")
        self.assertEqual(normalize_role("backend"), "backend")


if __name__ == "__main__":
    unittest.main()
