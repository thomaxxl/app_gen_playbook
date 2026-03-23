from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_role_prompt import build_canonical_outputs, build_read_paths, parse_message_headers, parse_message_sections


class BuildRolePromptTests(unittest.TestCase):
    def test_requested_outputs_completed_alias_stops_required_read_bleed(self) -> None:
        sections = parse_message_sections(
            "\n".join(
                [
                    "from: frontend",
                    "to: architect",
                    "",
                    "## Required Reads",
                    "- runs/current/artifacts/ux/navigation.md",
                    "",
                    "## Requested Outputs Completed",
                    "- confirm implementation is ready",
                    "",
                    "## Implementation Evidence",
                    "- app/frontend/src/App.tsx",
                    "",
                    "## Blocking Issues",
                    "- none",
                ]
            )
        )

        self.assertEqual(
            sections["required reads"],
            ["runs/current/artifacts/ux/navigation.md"],
        )
        self.assertEqual(
            sections["requested outputs"],
            ["confirm implementation is ready"],
        )
        self.assertEqual(
            sections["implementation evidence"],
            ["app/frontend/src/App.tsx"],
        )
        self.assertEqual(sections["blocking issues"], ["none"])

    def test_gate_status_header_alias_is_promoted_into_sections(self) -> None:
        sections = parse_message_sections(
            "\n".join(
                [
                    "sender: architect",
                    "receiver: frontend",
                    "gate status: pass with assumptions",
                    "",
                    "## Required Reads",
                    "- runs/current/artifacts/architecture/overview.md",
                ]
            )
        )

        self.assertEqual(sections["gate status"], "pass with assumptions")
        self.assertEqual(
            sections["required reads"],
            ["runs/current/artifacts/architecture/overview.md"],
        )

    def test_prompt_instructions_require_process_cleanup(self) -> None:
        source = (Path(__file__).resolve().parent / "build_role_prompt.py").read_text(encoding="utf-8")

        self.assertIn("do not leave background servers, watchers, or helper processes running", source)
        self.assertIn("terminate any processes you started for this turn", source)
        self.assertIn("keeps only durable context relevant to future turns or future runs", source)
        self.assertIn("Forbidden writes:", source)

    def test_canonical_outputs_extract_evidence_paths_from_requested_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            read_paths: list[str] = []
            sections = {
                "requested outputs": [
                    "update runs/current/evidence/qa-delivery-review.md",
                    "write app/run.sh notes",
                ]
            }

            outputs = build_canonical_outputs(repo_root, "qa", read_paths, sections)

            self.assertIn("runs/current/evidence/qa-delivery-review.md", outputs)

    def test_build_read_paths_prefers_manifest_bundle_resolution_over_full_role_file(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        message_text = "\n".join(
            [
                "from: orchestrator",
                "to: frontend",
                "",
                "## Required Reads",
                "- playbook/task-bundles/frontend-implementation.yaml",
            ]
        )
        headers = parse_message_headers(message_text)
        sections = parse_message_sections(message_text, headers=headers)
        message_path = repo_root / "tools" / "testdata-build-role-prompt-message.md"
        message_path.write_text(message_text, encoding="utf-8")
        self.addCleanup(message_path.unlink)

        read_paths = build_read_paths(repo_root, "frontend", message_path, headers, sections)

        self.assertIn("playbook/index.md", read_paths)
        self.assertIn("playbook/task-bundles/frontend-implementation.yaml", read_paths)
        self.assertIn("playbook/process/read-sets/frontend-implementation-core.md", read_paths)
        self.assertNotIn("playbook/roles/frontend.md", read_paths)
        self.assertNotIn("runs/current/role-state/frontend/context.md", read_paths)


if __name__ == "__main__":
    unittest.main()
