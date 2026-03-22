from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validators.coverage.compile_product_scope import compile_product_scope_payload
from validators.coverage.validate_acceptance_review_coverage import collect_issues as collect_acceptance_review_coverage_issues
from validators.coverage.validate_frontend_route_coverage import collect_issues as collect_frontend_route_coverage_issues
from validators.coverage.validate_integration_review_coverage import collect_issues as collect_integration_review_coverage_issues
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
                "# User Story Catalog",
                "",
                "## Coverage Matrix",
                "",
                "| Actor | Discover/Search | Create/Intake | Inspect/Detail | Edit/Maintain | Workflow/Approval | Exception/Recovery | Reporting/Export | Admin/Setup | Covered by |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| Requester | yes | yes | yes | yes | no | yes | no | no | US-001 |",
                "| Approver | yes | no | yes | no | yes | yes | yes | no | US-004 |",
                "",
                "## Story Index",
                "",
                "| Story ID | Epic | Actor | Story Type | Priority | Release | Frequency | Criticality | Story Statement | Workflow IDs | Rule IDs | Resource IDs | Page IDs | Route IDs | Permission Context | Sample Data IDs | Acceptance IDs |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| US-001 | Overview | Requester | crud | must | R1 | daily | high | As a requester, I inspect the current overview and continue my work. | WF-001 | BR-001 | Run | PAGE-001 | N001 | requester can inspect assigned work | SD-001 | AC-001 |",
                "| US-004 | Approvals | Approver | approval | must | R1 | daily | high | As an approver, I review pending approvals and record a decision. | WF-003 | BR-004 | Approval | PAGE-006 | N007 | approver can review assigned approvals | SD-004 | AC-004 |",
                "",
                "## Detailed Stories",
                "",
                "### US-001 - Requester reviews overview",
                "- Context / trigger: Requester opens the home page.",
                "- Preconditions: The requester has at least one active item.",
                "- Happy path: The requester reviews the overview and opens the main action.",
                "- Alternate paths: The requester filters the overview to a secondary workstream.",
                "- Negative / validation paths: Invalid filter selections are rejected clearly.",
                "- Empty-state expectation: The overview explains what to do when no work exists.",
                "- Permission constraints: Only the assigned requester can inspect the work item.",
                "- Audit / notification expectation: View-only access does not emit a notification.",
                "- Non-goals: Bulk actions are out of scope.",
                "- Required evidence: Screenshot plus live route proof.",
                "",
                "### US-004 - Approver reviews pending request",
                "- Context / trigger: Approver opens the approvals queue.",
                "- Preconditions: At least one approval is pending.",
                "- Happy path: The approver opens the record and approves it.",
                "- Alternate paths: The approver rejects the record with a reason.",
                "- Negative / validation paths: Missing required rejection reason is blocked.",
                "- Empty-state expectation: Empty queue messaging is visible.",
                "- Permission constraints: Only assigned approvers can make a decision.",
                "- Audit / notification expectation: Approval writes an audit note and triggers notification.",
                "- Non-goals: Delegation is out of scope.",
                "- Required evidence: Screenshot plus live route proof.",
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
                "| Story ID | Priority | Story Type | Workflow IDs | Rule IDs | Page IDs | Route IDs | State/Mode Coverage | Permission Context | Sample Data IDs | Acceptance IDs | Generated resource allowed as satisfier? | Required preview evidence | Required live QA evidence | Acceptance owner |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| US-001 | must | crud | WF-001 | BR-001 | PAGE-001 | N001 | active, empty | requester can inspect assigned work | SD-001 | AC-001 | no | yes | yes | product_manager |",
                "| US-004 | must | approval | WF-003 | BR-004 | PAGE-006 | N007 | pending, approved, rejected | approver can review assigned approvals | SD-004 | AC-004 | no | yes | yes | product_manager |",
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
            self.assertEqual(payload["required_actor_coverage"], ["Approver", "Requester"])
            self.assertIn("approval", payload["story_type_catalog"])

    def test_compile_product_scope_fails_when_must_story_lacks_required_detail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            story_text = (repo_root / "runs/current/artifacts/product/user-stories.md").read_text(encoding="utf-8")
            write(
                repo_root / "runs/current/artifacts/product/user-stories.md",
                story_text.replace("- Empty-state expectation: Empty queue messaging is visible.\n", ""),
            )
            _, issues = compile_product_scope_payload(repo_root)
            self.assertTrue(any("US-004: detailed story section is missing 'Empty-state expectation:'" in issue for issue in issues))

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
                repo_root / "runs/current/evidence/ui-previews/qa-manifest.md",
                "# QA Screenshot Manifest\n\ncapture_status: captured\n- reviewed_surfaces:\n  - `N001 Overview` at `/app/#/Home` -> `qa-n001-home.png`\n",
            )
            write(
                repo_root / "runs/current/evidence/qa-delivery-review.md",
                "- source manifest: `runs/current/evidence/ui-previews/qa-manifest.md`\n- `curl http://127.0.0.1:5180/app/#/Home` -> `200`\n",
            )
            issues = collect_qa_review_coverage_issues(repo_root)
            self.assertTrue(any("N007" in issue["reason"] for issue in issues))

    def test_qa_review_coverage_passes_when_review_and_manifest_cover_required_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            write(
                repo_root / "runs/current/evidence/ui-previews/qa-manifest.md",
                "\n".join(
                    [
                        "# QA Screenshot Manifest",
                        "",
                        "capture_status: captured",
                        "- reviewed_surfaces:",
                        "  - `N001 Overview` at `/app/#/Home` -> `qa-n001-home.png`",
                        "  - `N007 Reviews & Approvals` at `/app/#/approvals` -> `qa-n007-approvals.png`",
                        "",
                    ]
                ),
            )
            write(
                repo_root / "runs/current/evidence/qa-delivery-review.md",
                "\n".join(
                    [
                        "- source manifest: `runs/current/evidence/ui-previews/qa-manifest.md`",
                        "- covered stories: US-001 and US-004",
                        "- verified `/app/#/Home` live and reviewed `qa-n001-home.png`",
                        "- verified `/app/#/approvals` live and reviewed `qa-n007-approvals.png`",
                        "",
                    ]
                ),
            )
            issues = collect_qa_review_coverage_issues(repo_root)
            self.assertEqual(issues, [])

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

    def test_integration_review_coverage_fails_when_quality_evidence_is_still_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            write(
                repo_root / "runs/current/artifacts/architecture/integration-review.md",
                "\n".join(
                    [
                        "## Story Coverage",
                        "- US-001 and US-004 were reviewed against the delivered UI.",
                        "",
                        "## Actor Coverage",
                        "- Requester and Approver flows were both exercised.",
                        "",
                        "## Story Type Coverage",
                        "- crud and approval stories were both reviewed.",
                        "",
                        "## Scenario Depth Coverage",
                        "- happy path, alternate path, negative validation, empty state, and permission context were checked.",
                        "",
                        "## Page Coverage",
                        "- PAGE-001 and PAGE-006 were reviewed live.",
                        "",
                        "## Route Coverage",
                        "- N001 `/app/#/Home` and N007 `/app/#/approvals` were reviewed.",
                        "",
                    ]
                ),
            )
            write(
                repo_root / "runs/current/evidence/quality/quality-summary.md",
                "# Quality Summary\n\n## Decision\n\nThe reconciled Phase 6 quality evidence pack is `blocked`.\n",
            )
            write(
                repo_root / "runs/current/evidence/quality/crud-matrix.md",
                "# CRUD Matrix\n\n## Gate C status\n\nCurrent CRUD evidence status: `blocked`.\n",
            )

            issues = collect_integration_review_coverage_issues(repo_root)
            reasons = [issue["reason"] for issue in issues]
            self.assertTrue(any("quality evidence pack is blocked" in reason for reason in reasons))
            self.assertTrue(any("CRUD evidence is blocked" in reason for reason in reasons))

    def test_acceptance_review_coverage_fails_when_quality_evidence_is_still_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            write(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "\n".join(
                    [
                        "## Story Coverage",
                        "- US-001 and US-004 are accepted against the delivered behavior.",
                        "",
                        "## Actor Coverage",
                        "- Requester and Approver coverage is acceptable.",
                        "",
                        "## Story Type Coverage",
                        "- crud and approval scope was reviewed.",
                        "",
                        "## Scenario Depth Coverage",
                        "- happy path, alternate path, negative validation, empty state, and permission context were checked.",
                        "",
                        "## Page Coverage",
                        "- PAGE-001 and PAGE-006 are covered.",
                        "",
                        "## Route Coverage",
                        "- N001 `/app/#/Home` and N007 `/app/#/approvals` are covered.",
                        "",
                    ]
                ),
            )
            write(
                repo_root / "runs/current/evidence/quality/quality-summary.md",
                "# Quality Summary\n\n## Decision\n\nThe reconciled Phase 6 quality evidence pack is `blocked`.\n",
            )
            write(
                repo_root / "runs/current/evidence/quality/crud-matrix.md",
                "# CRUD Matrix\n\n## Gate C status\n\nCurrent CRUD evidence status: `blocked`.\n",
            )

            issues = collect_acceptance_review_coverage_issues(repo_root)
            reasons = [issue["reason"] for issue in issues]
            self.assertTrue(any("quality evidence pack is blocked" in reason for reason in reasons))
            self.assertTrue(any("CRUD evidence is blocked" in reason for reason in reasons))

    def test_acceptance_review_coverage_fails_when_story_sections_are_hand_wavy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            write(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "\n".join(
                    [
                        "## Story Coverage",
                        "pending",
                        "",
                        "## Actor Coverage",
                        "pending",
                        "",
                        "## Story Type Coverage",
                        "pending",
                        "",
                        "## Scenario Depth Coverage",
                        "pending",
                        "",
                        "## Page Coverage",
                        "pending",
                        "",
                        "## Route Coverage",
                        "pending",
                        "",
                    ]
                ),
            )
            issues = collect_acceptance_review_coverage_issues(repo_root)
            reasons = [issue["reason"] for issue in issues]
            self.assertTrue(any("empty or hand-wavy" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
