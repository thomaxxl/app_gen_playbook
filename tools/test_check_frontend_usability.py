from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_frontend_usability import collect_issues


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CheckFrontendUsabilityTests(unittest.TestCase):
    def test_accepts_expected_entry_and_custom_cta_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            for rel in (
                "runs/current/artifacts/ux/resource-view-strategy.md",
                "runs/current/artifacts/ux/relationship-surface-plan.md",
                "runs/current/artifacts/ux/dashboard-data-plan.md",
                "runs/current/artifacts/ux/form-grouping-plan.md",
            ):
                write_file(repo_root / rel, "# Ready\n")
            write_file(
                repo_root / "runs/current/artifacts/ux/landing-strategy.md",
                "\n".join(
                    [
                        "- Entry-page title: `Library Overview`",
                        "- Primary CTA label: `Add Song`",
                    ]
                ),
            )
            write_file(
                repo_root / "runs/current/artifacts/ux/custom-view-specs.md",
                "\n".join(
                    [
                        "### `Home`",
                        "- Action row: `Add Song`, `Review Curation Queue`, `Create Playlist`",
                        "",
                        "### `Curation Queue`",
                        "- Action row: `Open next song`, `Open Songs`, `Back to Home`",
                    ]
                ),
            )
            write_file(
                repo_root / "app/frontend/src/App.jsx",
                "\n".join(
                    [
                        'export default function App() {',
                        '  return "Library Overview Add Song Review Curation Queue Create Playlist Open next song Open Songs Back to Home";',
                        "}",
                    ]
                ),
            )

            self.assertEqual(collect_issues(repo_root), [])

    def test_flags_missing_primary_cta_and_recovery_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            for rel in (
                "runs/current/artifacts/ux/resource-view-strategy.md",
                "runs/current/artifacts/ux/relationship-surface-plan.md",
                "runs/current/artifacts/ux/dashboard-data-plan.md",
                "runs/current/artifacts/ux/form-grouping-plan.md",
            ):
                write_file(repo_root / rel, "# Ready\n")
            write_file(
                repo_root / "runs/current/artifacts/ux/landing-strategy.md",
                "\n".join(
                    [
                        "- Entry-page title: `Library Overview`",
                        "- Primary CTA label: `Add Song`",
                    ]
                ),
            )
            write_file(
                repo_root / "runs/current/artifacts/ux/custom-view-specs.md",
                "### `Home`\n- Action row: `Add Song`\n",
            )
            write_file(
                repo_root / "app/frontend/src/App.jsx",
                'export default function App() { return "Frontend Contract Recovery"; }',
            )

            issues = collect_issues(repo_root)
            self.assertTrue(any("primary CTA label not found" in issue for issue in issues))
            self.assertTrue(any("forbidden recovery/debug copy" in issue for issue in issues))

    def test_flags_missing_new_ux_planning_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            write_file(
                repo_root / "runs/current/artifacts/ux/landing-strategy.md",
                "- Entry-page title: `Library Overview`\n- Primary CTA label: `Add Song`\n",
            )
            write_file(
                repo_root / "app/frontend/src/App.jsx",
                'export default function App() { return "Library Overview Add Song"; }',
            )

            issues = collect_issues(repo_root)
            self.assertTrue(any("resource-view-strategy.md" in issue for issue in issues))
            self.assertTrue(any("relationship-surface-plan.md" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
