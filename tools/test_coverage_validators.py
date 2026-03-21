from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validators.coverage.compile_product_scope import compile_product_scope_payload
from validators.coverage.validate_frontend_route_coverage import collect_issues as collect_frontend_route_coverage_issues
from validators.coverage.validate_preview_coverage import collect_issues as collect_preview_coverage_issues
from validators.coverage.validate_qa_review_coverage import collect_issues as collect_qa_review_coverage_issues


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def seed_scope(repo_root: Path) -> None:
    write(
        repo_root / "runs/current/artifacts/product/user-stories.md",
        "\n".join(
            [
                "| Story ID | Actor | Story | Priority | Workflow IDs | Resources | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- |",
                "| US-001 | PM | Overview | must | WF-001 | X | note |",
                "| US-004 | PM | Approvals | must | WF-003 | X | note |",
            ]
        )
        + "\n",
    )
    write(
        repo_root / "runs/current/artifacts/product/custom-pages.md",
        "\n".join(
            [
                "| Page ID | Purpose | Intended user | Why generated resource pages are insufficient | Entry behavior | Required data | Key actions or links | Success criteria |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
                "| PAGE-001 Overview | Purpose | PM | no | default | data | actions | success |",
                "| PAGE-006 Reviews & Approvals | Purpose | PM | no | nav | data | actions | success |",
            ]
        )
        + "\n",
    )
    write(
        repo_root / "runs/current/artifacts/product/traceability-matrix.md",
        "\n".join(
            [
                "| Story ID | Priority | Workflow IDs | Page IDs | Route IDs | Generated resource allowed as satisfier? | Required preview evidence | Required live QA evidence | Acceptance owner |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| US-001 | must | WF-001 | PAGE-001 | N001 | no | yes | yes | product_manager |",
                "| US-004 | must | WF-003 | PAGE-006 | N007 | no | yes | yes | product_manager |",
            ]
        )
        + "\n",
    )
    write(
        repo_root / "runs/current/artifacts/ux/navigation.md",
        "\n".join(
            [
                "| Route ID | Path | Label | Visibility | Implementation | Role | Purpose | Entry cue | Trigger | Back target | Primary action | Secondary action | Accessibility | Responsive | Delivery mode | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| N001 | `/app/#/Home` | Overview | visible | custom | primary-entry | purpose | cue | trigger | back | primary | secondary | a11y | responsive | custom | note |",
                "| N007 | `/app/#/approvals` | Reviews & Approvals | visible | custom | support | purpose | cue | trigger | back | primary | secondary | a11y | responsive | custom | note |",
            ]
        )
        + "\n",
    )
    write(
        repo_root / "runs/current/artifacts/ux/landing-strategy.md",
        "- Primary CTA route target: `/app/#/features` or `/app/#/features/:id`\n",
    )


class CoverageValidatorTests(unittest.TestCase):
    def test_compile_product_scope_requires_traceability_for_must_stories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            payload, issues = compile_product_scope_payload(repo_root)
            self.assertEqual(issues, [])
            self.assertEqual(len(payload["must_stories"]), 2)

    def test_frontend_route_coverage_fails_on_missing_required_route_and_wrong_cta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            write(
                repo_root / "app/frontend/src/App.tsx",
                'import { Resource, CustomRoutes } from "react-admin";\n'
                'import { Route } from "react-router-dom";\n'
                'export default function App(){return <><Resource name="Home" list={() => null} /><CustomRoutes><Route path="/Collection" element={null} /></CustomRoutes></>;}\n',
            )
            write(
                repo_root / "app/frontend/src/Home.tsx",
                'export default function Home(){ const primaryRoute = "/Collection"; return null; }\n',
            )
            issues = collect_frontend_route_coverage_issues(repo_root)
            reasons = [issue["reason"] for issue in issues]
            self.assertTrue(any("missing required visible route N007" in reason for reason in reasons))
            self.assertTrue(any("Home primary CTA target drift" in reason for reason in reasons))

    def test_preview_coverage_fails_when_manifest_reviews_subset_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            write(
                repo_root / "runs/current/evidence/ui-previews/manifest.md",
                "# UI Preview Manifest\n\ncapture_status: captured\n- reviewed_surfaces:\n  - `Home desktop` at `/app/#/Home` -> `home.png`\n",
            )
            issues = collect_preview_coverage_issues(repo_root)
            self.assertTrue(any("N007" in issue["reason"] for issue in issues))

    def test_qa_review_coverage_fails_when_qa_only_mentions_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            write(
                repo_root / "runs/current/evidence/qa-delivery-review.md",
                "- `curl http://127.0.0.1:5180/app/#/Home` -> `200`\n",
            )
            issues = collect_qa_review_coverage_issues(repo_root)
            self.assertTrue(any("N007" in issue["reason"] for issue in issues))

    def test_frontend_route_coverage_prefers_active_change_candidate_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            write(
                repo_root / "runs/current/orchestrator/run-status.json",
                '{\n  "change_id": "CR-TEST-001"\n}\n',
            )
            write(
                repo_root / "runs/current/changes/CR-TEST-001/candidate/artifacts/product/custom-pages.md",
                "\n".join(
                    [
                        "| Page ID | Purpose | Intended user | Why generated resource pages are insufficient | Entry behavior | Required data | Key actions or links | Success criteria |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| PAGE-CR-001 Run Overview | Purpose | PM | no | default | data | actions | success |",
                        "| PAGE-CR-004 Handoffs & Messages | Purpose | PM | no | nav | data | actions | success |",
                    ]
                )
                + "\n",
            )
            write(
                repo_root / "runs/current/changes/CR-TEST-001/candidate/artifacts/ux/navigation.md",
                "\n".join(
                    [
                        "| Route ID | Path | Label | Visibility | Implementation | Role | Purpose | Entry cue | Trigger | Back target | Primary action | Secondary action | Accessibility | Responsive | Delivery mode | Notes |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| N201 | `/#/overview` | Run Overview | visible | custom | primary-entry | purpose | cue | trigger | back | primary | secondary | a11y | responsive | custom | note |",
                        "| N202 | `/#/handoffs` | Handoffs & Messages | visible | custom | support | purpose | cue | trigger | back | primary | secondary | a11y | responsive | custom | note |",
                    ]
                )
                + "\n",
            )
            write(
                repo_root / "runs/current/changes/CR-TEST-001/candidate/artifacts/ux/landing-strategy.md",
                "# Landing Strategy Delta\n\n- Primary CTA: open the pending handoff queue for the current run.\n",
            )
            write(
                repo_root / "app/frontend/src/App.tsx",
                'import { CustomRoutes } from "react-admin";\n'
                'import { Route } from "react-router-dom";\n'
                'export default function App(){return <CustomRoutes><Route path="/overview" element={null} /><Route path="/handoffs" element={null} /></CustomRoutes>;}\n',
            )
            write(
                repo_root / "app/frontend/src/Home.tsx",
                'export default function Home(){ const primaryRoute = "/handoffs"; return null; }\n',
            )

            payload, issues = compile_product_scope_payload(repo_root)
            self.assertEqual(issues, [])
            self.assertIn(
                "runs/current/changes/CR-TEST-001/candidate/artifacts/ux/navigation.md",
                payload["source_paths"],
            )
            self.assertEqual(
                [route["path"] for route in payload["required_visible_routes"]],
                ["/app/#/overview", "/app/#/handoffs"],
            )

            route_issues = collect_frontend_route_coverage_issues(repo_root)
            self.assertEqual(route_issues, [])


if __name__ == "__main__":
    unittest.main()
