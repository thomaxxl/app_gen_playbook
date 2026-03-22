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
from validators.coverage.validate_product_scope_contracts import collect_issues as collect_product_scope_contract_issues
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
                "| Actor | Discover/Search | Create/Intake | Inspect/Detail | Edit/Maintain | Workflow/Approval | Exception/Recovery | Reporting/Export | Admin/Setup |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| Requester | yes | no | yes | no | no | no | no | no |",
                "| Approver | no | no | yes | no | yes | yes | no | no |",
                "",
                "## Capability Coverage",
                "",
                "| Actor | Capability Band | Covered by Story IDs |",
                "| --- | --- | --- |",
                "| Requester | Discover/Search | US-001 |",
                "| Requester | Inspect/Detail | US-001 |",
                "| Approver | Inspect/Detail | US-004 |",
                "| Approver | Workflow/Approval | US-004 |",
                "| Approver | Exception/Recovery | US-004 |",
                "",
                "## Story Index",
                "",
                "| Story ID | Title | Actor | Priority | Delivery Class | Release | Story Type | Story Statement |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
                "| US-001 | Requester overview | Requester | P1 | must | R1 | crud | As a requester, I inspect the current overview and continue my work. |",
                "| US-004 | Approver reviews pending request | Approver | P1 | must | R1 | approval | As an approver, I review pending approvals and record a decision. |",
                "",
                "## User Scenarios & Testing",
                "",
                "### US-001 - Requester reviews overview (Priority: P1)",
                "**Actor**: Requester",
                "**Story Type**: crud",
                "**Release**: R1",
                "",
                "As a requester, I inspect the current overview and continue my work.",
                "",
                "**Why this priority**: The overview is the first stop for the current release.",
                "**Independent Test**: Open the home overview as a requester and confirm the assigned work summary and primary next step render correctly.",
                "",
                "**Acceptance Scenarios**:",
                "1. **Given** the requester has active work **When** the requester opens the overview **Then** the current work summary and primary CTA are visible.",
                "",
                "**Edge Cases**:",
                "- the requester has no active work and the page must explain what to do next",
                "",
                "Context / trigger: Requester opens the home page.",
                "Preconditions: The requester has at least one active item.",
                "Happy path: The requester reviews the overview and opens the main action.",
                "Alternate paths: The requester switches to a secondary workstream summary.",
                "Negative / validation paths: Invalid filter selections are rejected clearly.",
                "Empty-state expectation: The overview explains what to do when no work exists.",
                "Permission constraints: Only the assigned requester can inspect the work item.",
                "Audit / notification expectation: View-only access does not emit a notification.",
                "Non-goals: Bulk actions are out of scope.",
                "Required evidence: Screenshot plus live route proof.",
                "",
                "### US-004 - Approver reviews pending request (Priority: P1)",
                "**Actor**: Approver",
                "**Story Type**: approval",
                "**Release**: R1",
                "",
                "As an approver, I review pending approvals and record a decision.",
                "",
                "**Why this priority**: Pending approvals are the control point before work can continue.",
                "**Independent Test**: Open one pending approval, approve or reject it, and confirm the queue and audit trail update correctly.",
                "",
                "**Acceptance Scenarios**:",
                "1. **Given** a pending approval assigned to the approver **When** the approver records a decision **Then** the queue and audit trail update correctly.",
                "",
                "**Edge Cases**:",
                "- the queue is empty and must show a useful empty-state",
                "",
                "Context / trigger: Approver opens the approvals queue.",
                "Preconditions: At least one approval is pending.",
                "Happy path: The approver opens the record and approves it.",
                "Alternate paths: The approver rejects the record with a reason.",
                "Negative / validation paths: Missing required rejection reason is blocked.",
                "Empty-state expectation: Empty queue messaging is visible.",
                "Permission constraints: Only assigned approvers can make a decision.",
                "Audit / notification expectation: Approval writes an audit note and triggers notification.",
                "Non-goals: Delegation is out of scope.",
                "Required evidence: Screenshot plus live route proof.",
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
                "| Story ID | Concept IDs | Workflow IDs | Business Event IDs | Rule IDs | Resource IDs | Primary Evidence Mode | Page IDs | Route IDs | State/Mode Coverage | Permission Context | Sample Data IDs | Acceptance IDs | Generated resource allowed as satisfier? | Required preview evidence | Required live QA evidence | Acceptance owner |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| US-001 | C-001 | WF-001 | none | BR-001 | Run | ui | PAGE-001 | N001 | active, empty | requester can inspect assigned work | SD-001 | AC-001 | no | yes | yes | product_manager |",
                "| US-004 | C-004 | WF-003 | EV-004 | BR-004 | Approval | ui | PAGE-006 | N007 | pending, approved, rejected | approver can review assigned approvals | SD-004 | AC-004 | no | yes | yes | product_manager |",
            ]
        )
        + "\n",
    )
    write(
        repo_root / "runs/current/artifacts/product/story-quality-checklist.md",
        "\n".join(
            [
                "# Story Quality Checklist",
                "",
                "- status: reviewed",
                "- current-release stories checked: US-001, US-004",
                "- normalized capability coverage: aligned",
                "- story-core completeness: pass",
                "- critical issues: none",
                "- review_summary: The story catalog is concrete, independently testable, and aligned with traceability.",
                "",
            ]
        ),
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
    def test_compile_product_scope_requires_traceability_for_current_release_stories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            payload, issues = compile_product_scope_payload(repo_root)
            self.assertEqual(issues, [])
            self.assertEqual(len(payload["current_release_stories"]), 2)
            self.assertEqual(payload["required_actor_coverage"], ["Approver", "Requester"])
            self.assertIn("approval", payload["story_type_catalog"])

    def test_compile_product_scope_requires_concept_mapping_for_current_release_stories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            trace_text = (repo_root / "runs/current/artifacts/product/traceability-matrix.md").read_text(encoding="utf-8")
            write(
                repo_root / "runs/current/artifacts/product/traceability-matrix.md",
                trace_text.replace("| US-001 | C-001 |", "| US-001 | none |"),
            )

            _, issues = compile_product_scope_payload(repo_root)
            self.assertTrue(any("US-001: current-release story is missing concept mapping" in issue for issue in issues))

    def test_compile_product_scope_accepts_transitional_traceability_header_for_non_current_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            story_text = (repo_root / "runs/current/artifacts/product/user-stories.md").read_text(encoding="utf-8")
            story_text = story_text.replace("| US-001 | Requester overview | Requester | P1 | must | R1 |", "| US-001 | Requester overview | Requester | P1 | must | R2 |")
            story_text = story_text.replace("| US-004 | Approver reviews pending request | Approver | P1 | must | R1 |", "| US-004 | Approver reviews pending request | Approver | P1 | must | R2 |")
            write(repo_root / "runs/current/artifacts/product/user-stories.md", story_text)

            write(
                repo_root / "runs/current/artifacts/product/traceability-matrix.md",
                "\n".join(
                    [
                        "| Story ID | Workflow IDs | Rule IDs | Resource IDs | Primary Evidence Mode | Page IDs | Route IDs | State/Mode Coverage | Permission Context | Sample Data IDs | Acceptance IDs | Generated resource allowed as satisfier? | Required preview evidence | Required live QA evidence | Acceptance owner |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| US-001 | WF-001 | BR-001 | Run | ui | PAGE-001 | N001 | active, empty | requester can inspect assigned work | SD-001 | AC-001 | no | yes | yes | product_manager |",
                        "| US-004 | WF-003 | BR-004 | Approval | ui | PAGE-006 | N007 | pending, approved, rejected | approver can review assigned approvals | SD-004 | AC-004 | no | yes | yes | product_manager |",
                    ]
                )
                + "\n",
            )

            payload, issues = compile_product_scope_payload(repo_root)
            self.assertFalse(any("must use exact columns" in issue for issue in issues))
            self.assertEqual(payload["current_release_stories"], [])

    def test_compile_product_scope_fails_when_current_release_story_lacks_required_detail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            story_text = (repo_root / "runs/current/artifacts/product/user-stories.md").read_text(encoding="utf-8")
            write(
                repo_root / "runs/current/artifacts/product/user-stories.md",
                story_text.replace("Empty-state expectation: Empty queue messaging is visible.\n", ""),
            )
            _, issues = compile_product_scope_payload(repo_root)
            self.assertTrue(any("US-004: higher-depth story block is missing 'Empty-state expectation:'" in issue for issue in issues))

    def test_compile_product_scope_requires_capability_coverage_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            story_text = (repo_root / "runs/current/artifacts/product/user-stories.md").read_text(encoding="utf-8")
            capability_section = (
                "## Capability Coverage\n\n"
                "| Actor | Capability Band | Covered by Story IDs |\n"
                "| --- | --- | --- |\n"
                "| Requester | Discover/Search | US-001 |\n"
                "| Requester | Inspect/Detail | US-001 |\n"
                "| Approver | Inspect/Detail | US-004 |\n"
                "| Approver | Workflow/Approval | US-004 |\n"
                "| Approver | Exception/Recovery | US-004 |\n\n"
            )
            write(
                repo_root / "runs/current/artifacts/product/user-stories.md",
                story_text.replace(capability_section, ""),
            )

            _, issues = compile_product_scope_payload(repo_root)
            self.assertTrue(any("capability coverage is missing or empty" in issue for issue in issues))

    def test_compile_product_scope_requires_story_core_block_for_each_current_release_story(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            story_text = (repo_root / "runs/current/artifacts/product/user-stories.md").read_text(encoding="utf-8")
            story_text = story_text.replace(
                "| US-004 | Approver reviews pending request | Approver | P1 | must | R1 | approval | As an approver, I review pending approvals and record a decision. |\n",
                "| US-004 | Approver reviews pending request | Approver | P2 | should | R1 | reporting-search | As an approver, I review pending approvals and record a decision. |\n",
            )
            start = story_text.index("### US-004 - Approver reviews pending request (Priority: P1)")
            write(
                repo_root / "runs/current/artifacts/product/user-stories.md",
                story_text[:start].rstrip() + "\n",
            )

            _, issues = compile_product_scope_payload(repo_root)
            self.assertTrue(any("US-004: missing required current-release story block" in issue for issue in issues))

    def test_compile_product_scope_allows_non_ui_story_types_with_background_evidence_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            story_text = (repo_root / "runs/current/artifacts/product/user-stories.md").read_text(encoding="utf-8")
            story_text = story_text.replace(
                "| Approver | no | no | yes | no | yes | yes | no | no |\n",
                "| Approver | no | no | yes | no | yes | yes | yes | no |\n",
            )
            story_text = story_text.replace(
                "| Approver | Exception/Recovery | US-004 |\n",
                "| Approver | Exception/Recovery | US-004 |\n| Approver | Reporting/Export | US-050 |\n",
            )
            story_text = story_text.replace(
                "| US-004 | Approver reviews pending request | Approver | P1 | must | R1 | approval | As an approver, I review pending approvals and record a decision. |\n",
                "| US-004 | Approver reviews pending request | Approver | P1 | must | R1 | approval | As an approver, I review pending approvals and record a decision. |\n"
                "| US-050 | Approver receives audit notification | Approver | P2 | should | R1 | notification-audit | As an approver, I confirm the audit notification stream records approval outcomes. |\n",
            )
            story_text += "\n".join(
                [
                    "",
                    "### US-050 - Approver receives audit notification (Priority: P2)",
                    "**Actor**: Approver",
                    "**Story Type**: notification-audit",
                    "**Release**: R1",
                    "",
                    "As an approver, I confirm the audit notification stream records approval outcomes.",
                    "",
                    "**Why this priority**: Audit visibility is required in the first release but does not need a dedicated UI route.",
                    "**Independent Test**: Complete an approval and confirm the audit notification record is emitted for downstream observers.",
                    "",
                    "**Acceptance Scenarios**:",
                    "1. **Given** an approval is completed **When** the transaction commits **Then** the audit notification record exists for downstream review.",
                    "",
                    "**Edge Cases**:",
                    "- duplicate notifications are not emitted for the same approval action",
                    "",
                    "Context / trigger: An approval decision is committed.",
                    "Preconditions: An approval is ready to transition.",
                    "Happy path: The approval completes and the audit record is emitted.",
                    "Alternate paths: The approval is rejected and the rejection notification is emitted.",
                    "Negative / validation paths: Invalid approval state blocks the audit emission.",
                    "Empty-state expectation: No standalone UI surface is required for this story.",
                    "Permission constraints: Only authorized approval actions can emit the audit record.",
                    "Audit / notification expectation: The audit notification record is written exactly once.",
                    "Non-goals: Building a dedicated audit dashboard is out of scope.",
                    "Required evidence: Transaction proof plus downstream audit record validation.",
                    "",
                ]
            )
            write(repo_root / "runs/current/artifacts/product/user-stories.md", story_text)

            trace_text = (repo_root / "runs/current/artifacts/product/traceability-matrix.md").read_text(encoding="utf-8")
            trace_text += "| US-050 | C-050 | WF-050 | none | BR-050 | AuditEvent | background | none | none | emitted, duplicated-blocked | approver action emits audit record | SD-050 | AC-050 | no | no | no | product_manager |\n"
            write(repo_root / "runs/current/artifacts/product/traceability-matrix.md", trace_text)

            payload, issues = compile_product_scope_payload(repo_root)
            self.assertEqual(issues, [])
            us_050 = next(story for story in payload["required_story_reviews"] if story["story_id"] == "US-050")
            self.assertFalse(us_050["ui_surface_required"])
            self.assertEqual(us_050["supporting_surface_ids"], [])

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
            self.assertTrue(any("missing required story-supporting route N007" in reason for reason in reasons))
            self.assertTrue(any("Home primary CTA target drift" in reason for reason in reasons))

    def test_product_scope_contracts_fail_when_story_quality_checklist_is_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            write(
                repo_root / "runs/current/artifacts/product/story-quality-checklist.md",
                "# Story Quality Checklist\n\n- status: pending\n- review_summary: pending\n",
            )
            issues = collect_product_scope_contract_issues(repo_root)
            self.assertTrue(any("story quality checklist" in issue["reason"] for issue in issues))

    def test_preview_coverage_fails_when_manifest_reviews_subset_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            seed_scope(repo_root)
            write(
                repo_root / "runs/current/evidence/ui-previews/manifest.md",
                "\n".join(
                    [
                        "# UI Preview Manifest",
                        "",
                        "capture_status: captured",
                        "content_validation_status: reviewed",
                        "frontend_validation: approved",
                        "architect_validation: approved",
                        "product_manager_validation: approved",
                        "review_conclusion: Reviewed the overview preview.",
                        "",
                        "## Story Preview Coverage",
                        "",
                        "| Story ID | Supporting Surface IDs | Screenshot Files | Coverage Status | Notes |",
                        "| --- | --- | --- | --- | --- |",
                        "| US-001 | N001, PAGE-001 | home.png | reviewed | Reviewed the overview proof surfaces. |",
                        "",
                    ]
                ),
            )
            issues = collect_preview_coverage_issues(repo_root)
            self.assertTrue(any("US-004" in issue["reason"] for issue in issues))

    def test_qa_review_coverage_fails_when_qa_only_mentions_home(self) -> None:
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
                        "",
                        "## Story Screenshot Coverage",
                        "",
                        "| Story ID | Supporting Surface IDs | Screenshot Files | Coverage Status | Notes |",
                        "| --- | --- | --- | --- | --- |",
                        "| US-001 | N001, PAGE-001 | qa-n001-home.png | captured | Captured the home overview surface. |",
                        "",
                    ]
                ),
            )
            write(
                repo_root / "runs/current/evidence/qa-delivery-review.md",
                "\n".join(
                    [
                        "source manifest: runs/current/evidence/ui-previews/qa-manifest.md",
                        "",
                        "## Story Live Coverage",
                        "",
                        "| Story ID | Live Status | Independent Test Result | Supporting Surface IDs | Screenshot Files | Notes |",
                        "| --- | --- | --- | --- | --- | --- |",
                        "| US-001 | pass | Home overview rendered and CTA was usable. | N001, PAGE-001 | qa-n001-home.png | QA exercised the overview path. |",
                        "",
                    ]
                ),
            )
            issues = collect_qa_review_coverage_issues(repo_root)
            self.assertTrue(any("US-004" in issue["reason"] for issue in issues))

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
                        "",
                        "## Story Screenshot Coverage",
                        "",
                        "| Story ID | Supporting Surface IDs | Screenshot Files | Coverage Status | Notes |",
                        "| --- | --- | --- | --- | --- |",
                        "| US-001 | N001, PAGE-001 | qa-n001-home.png | captured | Captured the overview surface. |",
                        "| US-004 | N007, PAGE-006 | qa-n007-approvals.png | captured | Captured the approvals surface. |",
                        "",
                    ]
                ),
            )
            write(
                repo_root / "runs/current/evidence/qa-delivery-review.md",
                "\n".join(
                    [
                        "source manifest: runs/current/evidence/ui-previews/qa-manifest.md",
                        "",
                        "## Story Live Coverage",
                        "",
                        "| Story ID | Live Status | Independent Test Result | Supporting Surface IDs | Screenshot Files | Notes |",
                        "| --- | --- | --- | --- | --- | --- |",
                        "| US-001 | pass | Overview loaded and CTA was verified. | N001, PAGE-001 | qa-n001-home.png | Live-tested requester overview path. |",
                        "| US-004 | pass | Approval queue and audit trail updated correctly. | N007, PAGE-006 | qa-n007-approvals.png | Live-tested approver path. |",
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
                repo_root / "runs/current/changes/CR-TEST-001/candidate/artifacts/product/user-stories.md",
                "\n".join(
                    [
                        "# User Story Catalog",
                        "",
                        "## Coverage Matrix",
                        "",
                        "| Actor | Discover/Search | Create/Intake | Inspect/Detail | Edit/Maintain | Workflow/Approval | Exception/Recovery | Reporting/Export | Admin/Setup |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| Operator | yes | no | yes | no | no | yes | no | no |",
                        "",
                        "## Capability Coverage",
                        "",
                        "| Actor | Capability Band | Covered by Story IDs |",
                        "| --- | --- | --- |",
                        "| Operator | Discover/Search | US-201 |",
                        "| Operator | Inspect/Detail | US-201 |",
                        "| Operator | Exception/Recovery | US-202 |",
                        "",
                        "## Story Index",
                        "",
                        "| Story ID | Title | Actor | Priority | Delivery Class | Release | Story Type | Story Statement |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| US-201 | Operator reviews run overview | Operator | P1 | must | R1 | crud | As an operator, I inspect the current run overview. |",
                        "| US-202 | Operator reviews handoffs | Operator | P1 | must | R1 | exception-recovery | As an operator, I inspect the handoff queue. |",
                        "",
                        "## User Scenarios & Testing",
                        "",
                        "### US-201 - Operator reviews run overview (Priority: P1)",
                        "**Actor**: Operator",
                        "**Story Type**: crud",
                        "**Release**: R1",
                        "",
                        "As an operator, I inspect the current run overview.",
                        "",
                        "**Why this priority**: The iteration must keep the run overview available.",
                        "**Independent Test**: Open the overview and confirm the current run summary loads.",
                        "",
                        "**Acceptance Scenarios**:",
                        "1. **Given** a current run exists **When** the operator opens the overview **Then** the current run summary is visible.",
                        "",
                        "**Edge Cases**:",
                        "- the run has no recent activity and the overview must still render",
                        "",
                        "Context / trigger: The operator lands on the overview.",
                        "Preconditions: A current run exists.",
                        "Happy path: The overview loads and shows the current run summary.",
                        "Alternate paths: The operator drills into a secondary panel.",
                        "Negative / validation paths: Invalid query state is handled clearly.",
                        "Empty-state expectation: Empty run states are explained.",
                        "Permission constraints: Only authorized operators can inspect the run.",
                        "Audit / notification expectation: Read-only inspection does not emit notifications.",
                        "Non-goals: Editing the run is out of scope.",
                        "Required evidence: Screenshot plus live route proof.",
                        "",
                        "### US-202 - Operator reviews handoffs (Priority: P1)",
                        "**Actor**: Operator",
                        "**Story Type**: exception-recovery",
                        "**Release**: R1",
                        "",
                        "As an operator, I inspect the handoff queue.",
                        "",
                        "**Why this priority**: Handoffs are the primary follow-up path in this change scope.",
                        "**Independent Test**: Open the handoffs view and confirm pending handoffs can be inspected.",
                        "",
                        "**Acceptance Scenarios**:",
                        "1. **Given** at least one handoff exists **When** the operator opens the handoffs view **Then** the queue is visible.",
                        "",
                        "**Edge Cases**:",
                        "- the queue is empty and must still explain next steps",
                        "",
                        "Context / trigger: The operator opens the handoffs view.",
                        "Preconditions: Handoffs are available or the empty state is configured.",
                        "Happy path: The operator reviews the queue and opens a handoff.",
                        "Alternate paths: The operator filters the queue.",
                        "Negative / validation paths: Invalid filter state is rejected clearly.",
                        "Empty-state expectation: Empty queue messaging remains usable.",
                        "Permission constraints: Only operators with queue access can inspect handoffs.",
                        "Audit / notification expectation: View-only inspection does not emit notifications.",
                        "Non-goals: Editing handoff contents is out of scope.",
                        "Required evidence: Screenshot plus live route proof.",
                    ]
                )
                + "\n",
            )
            write(
                repo_root / "runs/current/changes/CR-TEST-001/candidate/artifacts/product/traceability-matrix.md",
                "\n".join(
                    [
                        "| Story ID | Concept IDs | Workflow IDs | Business Event IDs | Rule IDs | Resource IDs | Primary Evidence Mode | Page IDs | Route IDs | State/Mode Coverage | Permission Context | Sample Data IDs | Acceptance IDs | Generated resource allowed as satisfier? | Required preview evidence | Required live QA evidence | Acceptance owner |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| US-201 | C-201 | WF-201 | none | none | Run | ui | PAGE-CR-001 | N201 | active, complete | operator can inspect current run state | SD-201 | AC-201 | no | yes | yes | product_manager |",
                        "| US-202 | C-202 | WF-202 | EV-202 | none | HandoffMessage | ui | PAGE-CR-004 | N202 | queued, empty | operator can inspect handoffs | SD-202 | AC-202 | no | yes | yes | product_manager |",
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
                        "| Story ID | Decision | Independent Test Evidence | Supporting Surface IDs | Scenario Coverage | Notes |",
                        "| --- | --- | --- | --- | --- | --- |",
                        "| US-001 | approved | Overview path rendered and CTA worked. | N001, PAGE-001 | happy-path, empty-state, permission-context | Reviewed requester overview flow. |",
                        "| US-004 | approved | Approval flow updated the queue and audit trail. | N007, PAGE-006 | happy-path, alternate-path, negative-validation, empty-state, permission-context | Reviewed approver flow. |",
                        "",
                        "## Actor Coverage",
                        "| Actor | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- |",
                        "| Requester | US-001 | Reviewed requester overview flow. |",
                        "| Approver | US-004 | Reviewed approver decision flow. |",
                        "",
                        "## Story Type Coverage",
                        "| Story Type | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- |",
                        "| crud | US-001 | Reviewed overview story. |",
                        "| approval | US-004 | Reviewed approval story. |",
                        "",
                        "## Scenario Depth Coverage",
                        "| Scenario Check | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- |",
                        "| happy-path | US-001, US-004 | Happy paths were exercised. |",
                        "| alternate-path | US-004 | Alternate approval path was reviewed. |",
                        "| negative-validation | US-004 | Missing rejection reason was validated. |",
                        "| empty-state | US-001, US-004 | Empty-state messaging was reviewed. |",
                        "| permission-context | US-001, US-004 | Role-based access behavior was reviewed. |",
                        "",
                        "## Page Coverage",
                        "| Page ID | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- |",
                        "| PAGE-001 | US-001 | Reviewed overview page. |",
                        "| PAGE-006 | US-004 | Reviewed approvals page. |",
                        "",
                        "## Route Coverage",
                        "| Route ID | Path | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- | --- |",
                        "| N001 | /app/#/Home | US-001 | Reviewed overview route. |",
                        "| N007 | /app/#/approvals | US-004 | Reviewed approvals route. |",
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
                        "| Story ID | Decision | Independent Test Evidence | Supporting Surface IDs | Scenario Coverage | Notes |",
                        "| --- | --- | --- | --- | --- | --- |",
                        "| US-001 | accepted | Overview path rendered and CTA worked. | N001, PAGE-001 | happy-path, empty-state, permission-context | Accepted requester overview flow. |",
                        "| US-004 | accepted | Approval flow updated the queue and audit trail. | N007, PAGE-006 | happy-path, alternate-path, negative-validation, empty-state, permission-context | Accepted approver flow. |",
                        "",
                        "## Actor Coverage",
                        "| Actor | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- |",
                        "| Requester | US-001 | Requester coverage accepted. |",
                        "| Approver | US-004 | Approver coverage accepted. |",
                        "",
                        "## Story Type Coverage",
                        "| Story Type | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- |",
                        "| crud | US-001 | Crud coverage accepted. |",
                        "| approval | US-004 | Approval coverage accepted. |",
                        "",
                        "## Scenario Depth Coverage",
                        "| Scenario Check | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- |",
                        "| happy-path | US-001, US-004 | Happy paths were accepted. |",
                        "| alternate-path | US-004 | Alternate approval path was accepted. |",
                        "| negative-validation | US-004 | Negative validation behavior was accepted. |",
                        "| empty-state | US-001, US-004 | Empty-state behavior was accepted. |",
                        "| permission-context | US-001, US-004 | Permission behavior was accepted. |",
                        "",
                        "## Page Coverage",
                        "| Page ID | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- |",
                        "| PAGE-001 | US-001 | Overview page accepted. |",
                        "| PAGE-006 | US-004 | Approvals page accepted. |",
                        "",
                        "## Route Coverage",
                        "| Route ID | Path | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- | --- |",
                        "| N001 | /app/#/Home | US-001 | Overview route accepted. |",
                        "| N007 | /app/#/approvals | US-004 | Approvals route accepted. |",
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
                        "| Story ID | Decision | Independent Test Evidence | Supporting Surface IDs | Scenario Coverage | Notes |",
                        "| --- | --- | --- | --- | --- | --- |",
                        "| US-001 | pending | pending | pending | pending | pending |",
                        "",
                        "## Actor Coverage",
                        "| Actor | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- |",
                        "| Requester | pending | pending |",
                        "",
                        "## Story Type Coverage",
                        "| Story Type | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- |",
                        "| crud | pending | pending |",
                        "",
                        "## Scenario Depth Coverage",
                        "| Scenario Check | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- |",
                        "| happy-path | pending | pending |",
                        "",
                        "## Page Coverage",
                        "| Page ID | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- |",
                        "| PAGE-001 | pending | pending |",
                        "",
                        "## Route Coverage",
                        "| Route ID | Path | Covered Story IDs | Evidence Summary |",
                        "| --- | --- | --- | --- |",
                        "| N001 | /app/#/Home | pending | pending |",
                        "",
                    ]
                ),
            )
            issues = collect_acceptance_review_coverage_issues(repo_root)
            reasons = [issue["reason"] for issue in issues]
            self.assertTrue(any("placeholder" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
