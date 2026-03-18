from __future__ import annotations

import unittest

from build_role_prompt import parse_message_sections


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


if __name__ == "__main__":
    unittest.main()
