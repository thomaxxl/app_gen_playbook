from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

from check_frontend_usability import collect_issues


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CheckFrontendUsabilityTests(unittest.TestCase):
    def seed_runtime_files(self, repo_root: Path) -> None:
        write_file(
            repo_root / "app/frontend/src/generated/uxModel.ts",
            "\n".join(
                [
                    "export const UX_MODEL = {",
                    "  entrySurface: { mode: 'dashboard' },",
                    "  resources: { Song: { listColumnBudget: 5, groupedForms: true } },",
                    "};",
                ]
            ),
        )
        write_file(
            repo_root / "app/frontend/src/shared-runtime/resourceRegistry.tsx",
            "\n".join(
                [
                    "import FormSection from '../FormSection';",
                    "import { getResourceUxConfig } from '../generated/uxModel';",
                    "const DEFAULT_LIST_COLUMN_BUDGET = 6;",
                    "function selectListDisplayItems() { return []; }",
                    "function buildResolvedFormSections() { return []; }",
                    "export function ResourceRegistry() {",
                    "  getResourceUxConfig('Song');",
                    "  selectListDisplayItems();",
                    "  buildResolvedFormSections();",
                    "  return <FormSection title=\"Song details\">Runtime shell</FormSection>;",
                    "}",
                ]
            ),
        )

    def seed_binding_reference(self, repo_root: Path, change_id: str = "CR-1") -> None:
        write_file(
            repo_root / "runs/current/orchestrator/run-status.json",
            json.dumps({"change_id": change_id}) + "\n",
        )
        write_file(
            repo_root / f"runs/current/changes/{change_id}/external-references/manifest.json",
            json.dumps(
                {
                    "priority_order": [
                        "input-prompt",
                        "business-model-and-contracts",
                        "external-references",
                        "agent-interpretation",
                    ],
                    "references": [
                        {
                            "category": "visual-ui",
                            "fidelity": "mimic-look-and-feel",
                            "source_path": "/tmp/sonic.zip",
                        }
                    ],
                }
            )
            + "\n",
        )

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
            self.seed_runtime_files(repo_root)

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
            self.seed_runtime_files(repo_root)

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

    def test_flags_missing_ux_model_and_runtime_hooks(self) -> None:
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
                "- Entry-page title: `Library Overview`\n- Primary CTA label: `Add Song`\n",
            )
            write_file(
                repo_root / "app/frontend/src/App.jsx",
                'export default function App() { return "Library Overview Add Song"; }',
            )
            write_file(
                repo_root / "app/frontend/src/shared-runtime/resourceRegistry.tsx",
                'export function ResourceRegistry() { const displayItems = visibleDisplayItems(resourceMeta, "list"); return null; }',
            )

            issues = collect_issues(repo_root)
            self.assertTrue(any("generated/uxModel.ts" in issue for issue in issues))
            self.assertTrue(any("every visible list item" in issue for issue in issues))

    def test_flags_literal_raw_id_sources(self) -> None:
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
                "- Entry-page title: `Library Overview`\n- Primary CTA label: `Add Song`\n",
            )
            write_file(
                repo_root / "app/frontend/src/App.jsx",
                'export default function App() { return "Library Overview Add Song"; }',
            )
            write_file(
                repo_root / "app/frontend/src/generated/uxModel.ts",
                "export const UX_MODEL = { entrySurface: { mode: 'dashboard' }, resources: { Song: {} } };",
            )
            write_file(
                repo_root / "app/frontend/src/shared-runtime/resourceRegistry.tsx",
                "\n".join(
                    [
                        "import FormSection from '../FormSection';",
                        "import { getResourceUxConfig } from '../generated/uxModel';",
                        "const DEFAULT_LIST_COLUMN_BUDGET = 6;",
                        "function selectListDisplayItems() { return []; }",
                        "function buildResolvedFormSections() { return []; }",
                        'export function ResourceRegistry() { return <TextField source=\"artist_id\" />; }',
                    ]
                ),
            )

            issues = collect_issues(repo_root)
            self.assertTrue(any("raw _id" in issue for issue in issues))

    def test_requires_reference_alignment_for_binding_external_ui_reference(self) -> None:
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
                "- Entry-page title: `Library Overview`\n- Primary CTA label: `Add Song`\n",
            )
            write_file(
                repo_root / "app/frontend/src/App.jsx",
                'export default function App() { return "Library Overview Add Song"; }',
            )
            self.seed_runtime_files(repo_root)
            self.seed_binding_reference(repo_root)

            issues = collect_issues(repo_root)
            self.assertTrue(any("reference-alignment" in issue for issue in issues))

    def test_accepts_reference_alignment_when_binding_external_ui_reference_exists(self) -> None:
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
                "- Entry-page title: `Library Overview`\n- Primary CTA label: `Add Song`\n",
            )
            write_file(
                repo_root / "app/frontend/src/App.jsx",
                'export default function App() { return "Library Overview Add Song"; }',
            )
            self.seed_runtime_files(repo_root)
            self.seed_binding_reference(repo_root)
            write_file(
                repo_root / "runs/current/changes/CR-1/candidate/artifacts/ux/reference-alignment.md",
                "\n".join(
                    [
                        "# External Reference Alignment",
                        "",
                        "- input prompt",
                        "- business model",
                        "- external references",
                        "- agent interpretation",
                        "- shell",
                        "- palette",
                        "- typography",
                    ]
                )
                + "\n",
            )

            issues = collect_issues(repo_root)
            self.assertFalse(any("reference-alignment" in issue for issue in issues))

    def test_flags_decorative_search_input_without_real_search_behavior(self) -> None:
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
                "- Entry-page title: `Library Overview`\n- Primary CTA label: `Add Song`\n",
            )
            write_file(
                repo_root / "app/frontend/src/App.tsx",
                "\n".join(
                    [
                        'import InputBase from "@mui/material/InputBase";',
                        "export default function App() {",
                        '  return <InputBase placeholder="Search operations..." />;',
                        "}",
                    ]
                ),
            )
            self.seed_runtime_files(repo_root)

            issues = collect_issues(repo_root)
            self.assertTrue(any("search input appears decorative" in issue for issue in issues))

    def test_accepts_wired_search_input(self) -> None:
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
                "- Entry-page title: `Library Overview`\n- Primary CTA label: `Add Song`\n",
            )
            write_file(
                repo_root / "app/frontend/src/App.tsx",
                "\n".join(
                    [
                        'import InputBase from "@mui/material/InputBase";',
                        'import { useSearchParams } from "react-router-dom";',
                        "export default function App() {",
                        "  const [searchParams] = useSearchParams();",
                        "  void searchParams;",
                        "  return (",
                        '    <form onSubmit={() => {}}>',
                        '      <InputBase placeholder=\"Search operations...\" onChange={() => {}} />',
                        "    </form>",
                        "  );",
                        "}",
                    ]
                ),
            )
            self.seed_runtime_files(repo_root)

            issues = collect_issues(repo_root)
            self.assertFalse(any("search input appears decorative" in issue for issue in issues))

    def test_flags_decorative_filter_strip_without_interactivity(self) -> None:
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
                "- Entry-page title: `Library Overview`\n- Primary CTA label: `Add Song`\n",
            )
            write_file(
                repo_root / "app/frontend/src/App.tsx",
                "\n".join(
                    [
                        'import Chip from "@mui/material/Chip";',
                        "function FilterStrip({ filters }) {",
                        "  return filters.map((filter) => (",
                        '    <Chip key={filter.label} label={filter.label} variant={filter.active ? "filled" : "outlined"} />',
                        "  ));",
                        "}",
                        "export default function App() {",
                        "  return <FilterStrip filters={[{ label: 'Queue state' }]} />;",
                        "}",
                    ]
                ),
            )
            self.seed_runtime_files(repo_root)

            issues = collect_issues(repo_root)
            self.assertTrue(any("filter/scope chips appear decorative" in issue for issue in issues))

    def test_flags_search_evidence_that_accepts_frontend_fallbacks(self) -> None:
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
                "- Entry-page title: `Library Overview`\n- Primary CTA label: `Add Song`\n",
            )
            write_file(
                repo_root / "app/frontend/src/SearchExperience.tsx",
                "\n".join(
                    [
                        "export function SearchExperience() {",
                        '  return <input type=\"search\" placeholder=\"Search operations...\" />;',
                        "}",
                    ]
                ),
            )
            write_file(
                repo_root / "runs/current/evidence/frontend-browser-proof.md",
                "\n".join(
                    [
                        "# Frontend Browser Proof",
                        "",
                        "search_result_humanization_validation: approved-with-frontend-fallbacks",
                    ]
                )
                + "\n",
            )
            write_file(
                repo_root / "runs/current/evidence/frontend-usability.md",
                "\n".join(
                    [
                        "# Frontend Usability",
                        "",
                        "human_readable_result_validation: approved-with-frontend-fallbacks",
                    ]
                )
                + "\n",
            )
            self.seed_runtime_files(repo_root)

            issues = collect_issues(repo_root)
            self.assertTrue(any("frontend-browser-proof accepts search fallback status" in issue for issue in issues))
            self.assertTrue(any("frontend-usability accepts search fallback status" in issue for issue in issues))
            self.assertTrue(any("search_query_alignment_validation" in issue for issue in issues))

    def test_accepts_search_evidence_with_explicit_relevance_and_alignment_approval(self) -> None:
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
                "- Entry-page title: `Library Overview`\n- Primary CTA label: `Add Song`\n",
            )
            write_file(
                repo_root / "app/frontend/src/SearchExperience.tsx",
                "\n".join(
                    [
                        'import { useSearchParams } from "react-router-dom";',
                        "export function SearchExperience() {",
                        "  const [searchParams, setSearchParams] = useSearchParams();",
                        "  void searchParams; void setSearchParams;",
                        "  return <input type=\"search\" placeholder=\"Search operations...\" onChange={() => {}} />;",
                        "}",
                    ]
                ),
            )
            write_file(
                repo_root / "runs/current/evidence/frontend-browser-proof.md",
                "\n".join(
                    [
                        "# Frontend Browser Proof",
                        "",
                        "search_result_humanization_validation: approved",
                        "search_scope_truthfulness_validation: approved",
                        "search_query_alignment_validation: approved",
                        "search_match_explainability_validation: approved",
                        "search_representative_query_validation: approved",
                    ]
                )
                + "\n",
            )
            write_file(
                repo_root / "runs/current/evidence/frontend-usability.md",
                "\n".join(
                    [
                        "# Frontend Usability",
                        "",
                        "search_ergonomics_validation: approved",
                        "human_readable_result_validation: approved",
                        "search_scope_truthfulness_validation: approved",
                        "search_query_alignment_validation: approved",
                        "search_match_explainability_validation: approved",
                        "search_relevance_validation: approved",
                    ]
                )
                + "\n",
            )
            self.seed_runtime_files(repo_root)

            issues = collect_issues(repo_root)
            self.assertFalse(any("search fallback status" in issue for issue in issues))
            self.assertFalse(any("search_query_alignment_validation" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
