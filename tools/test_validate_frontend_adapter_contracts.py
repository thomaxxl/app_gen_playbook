from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validators.policy.validate_frontend_adapter_contracts import (
    collect_adapter_lane_issues,
    collect_execute_usage_issues,
    collect_frontend_runtime_issues,
    collect_install_source_issues,
    collect_no_direct_fetch_issues,
    collect_relationship_route_issues,
    collect_search_wrapper_issues,
)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ValidateFrontendAdapterContractsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent

    def test_static_contract_validators_pass_on_repo(self) -> None:
        self.assertEqual(collect_adapter_lane_issues(self.repo_root), [])
        self.assertEqual(collect_install_source_issues(self.repo_root), [])
        self.assertEqual(collect_search_wrapper_issues(self.repo_root), [])
        self.assertEqual(collect_relationship_route_issues(self.repo_root), [])
        self.assertEqual(collect_execute_usage_issues(self.repo_root), [])
        self.assertEqual(collect_no_direct_fetch_issues(self.repo_root), [])

    def test_adapter_lane_validator_detects_missing_skill_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "playbook/process/read-sets/frontend-design-core.md",
                "# Frontend Design\n\n- ../../../specs/contracts/frontend/README.md\n",
            )
            for rel in (
                "playbook/process/read-sets/frontend-implementation-core.md",
                "playbook/process/read-sets/architect-authoring-core.md",
                "playbook/process/read-sets/architect-review-core.md",
                "playbook/roles/frontend.md",
                "playbook/roles/architect.md",
                "specs/contracts/frontend/runtime-contract.md",
                "templates/app/frontend/shared-runtime/admin/schemaContext.tsx.md",
            ):
                write_file(repo_root / rel, "placeholder\n")

            issues = collect_adapter_lane_issues(repo_root)
            self.assertTrue(
                any("skills/safrs-jsonapi-client-frontend/SKILL.md" in issue["reason"] for issue in issues)
            )

    def test_search_wrapper_validator_detects_legacy_avoid_package_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "templates/app/frontend/shared-runtime/admin/createSearchEnabledDataProvider.ts.md",
                'import { buildListQuery, normalizeDocument, getTotal, synthesizeCompositeKeys } from "safrs-jsonapi-client";\nThis template intentionally avoids `safrs-jsonapi-client`.\n',
            )
            write_file(
                repo_root / "specs/contracts/frontend/validation.md",
                "search-wrapper compatibility with package record shape `ja_type` `relationships`\n",
            )

            issues = collect_search_wrapper_issues(repo_root)
            self.assertTrue(any("still claims to avoid safrs-jsonapi-client" in issue["reason"] for issue in issues))

    def test_relationship_validator_detects_placeholder_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/contracts/frontend/relationship-ui.md",
                "canonical parent relationship routes how to build the parent relationship URL\n",
            )
            write_file(
                repo_root / "specs/contracts/frontend/validation.md",
                "relationship-route behavior is proven representative `dataProvider.execute(resource, params)` proof\n",
            )
            write_file(
                repo_root / "templates/app/frontend/shared-runtime/admin/resourceMetadata.ts.md",
                "relationshipRouteTemplate parentEndpoint includePath\n",
            )
            write_file(
                repo_root / "templates/app/frontend/shared-runtime/admin/schemaContext.tsx.md",
                'dataProvider.execute(resource, params) from "safrs-jsonapi-client"\n',
            )
            write_file(
                repo_root / "playbook/roles/frontend.md",
                "dataProvider.execute(resource, params)\ncomponent-level `fetch(...)`\n",
            )
            write_file(
                repo_root / "specs/contracts/frontend/custom-views.md",
                "dataProvider.execute(resource, params)\ndo not call `fetch(...)` directly\n",
            )
            write_file(
                repo_root / "templates/app/frontend/shared-runtime/relationshipUi.tsx.md",
                "\n".join(
                    (
                        "dataProvider.execute({",
                        "data-testid={`relationship-dialog-link:${surface}:",
                        "data-relationship-fetch-source",
                        "schema.resourceByType[relationship.parentResource]",
                        "normalizeEndpointToResource(relationship.parentEndpoint, schema)",
                        "return <div>{resource}</div>;",
                        "return <div>{relationship.label}</div>;",
                    )
                ),
            )
            write_file(
                repo_root / "templates/app/frontend/shared-runtime/resourceRegistry.tsx.md",
                'SimpleShowLayout\nsurface="list"\nsurface="summary"\nrelationship-tab-panel:tomany:\nrelationship-tab-panel:toone:\ndata-relationship-fetch-source\ngetRelatedRecordLabel(record, item.relationship, targetMeta)\n',
            )

            relationship_issues = collect_relationship_route_issues(repo_root)
            execute_issues = collect_execute_usage_issues(repo_root)
            self.assertTrue(any("legacy one-argument execute" in issue["reason"] for issue in relationship_issues))
            self.assertTrue(any("placeholder implementation text" in issue["reason"] for issue in relationship_issues))
            self.assertTrue(any("SimpleShowLayout" in issue["reason"] for issue in relationship_issues))
            self.assertTrue(any("parentEndpoint" in issue["reason"] or "schema.resourceByType[relationship.parentResource]" in issue["reason"] for issue in relationship_issues))
            self.assertTrue(any("plain text instead of RelatedRecordDialogLink" in issue["reason"] for issue in relationship_issues))
            self.assertTrue(any("execute(resource, params)" in issue["reason"] for issue in execute_issues))

    def test_runtime_validator_detects_missing_generated_runtime_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "app/frontend/src/shared-runtime/relationshipUi.tsx",
                "export function RelatedRecordSummary() { return <div>{resource}</div>; }\ndata-testid={`relationship-dialog-link:${surface}:}\ndata-relationship-fetch-source\n",
            )
            write_file(
                repo_root / "app/frontend/src/shared-runtime/resourceRegistry.tsx",
                "SimpleShowLayout\n",
            )
            write_file(
                repo_root / "app/frontend/tests/dataProvider.integration.test.ts",
                "describe('provider', () => {})\n",
            )
            write_file(
                repo_root / "runs/current/evidence/frontend-usability.md",
                "# Frontend Usability\n\nreview_status: approved\n",
            )
            write_file(
                repo_root / "runs/current/evidence/ui-previews/manifest.md",
                "# UI Preview Manifest\n\ncapture_status: captured\n",
            )
            write_file(
                repo_root / "runs/current/evidence/ui-previews/qa-manifest.md",
                "# QA Screenshot Manifest\n\ncapture_status: captured\n",
            )
            write_file(
                repo_root / "runs/current/evidence/qa-delivery-review.md",
                "# QA Delivery Review\n\nstatus: approved\n",
            )

            issues = collect_frontend_runtime_issues(repo_root)
            reasons = "\n".join(issue["reason"] for issue in issues)
            self.assertIn("generated relationship runtime is missing required token", reasons)
            self.assertIn("SimpleShowLayout", reasons)
            self.assertIn("do not exercise dataProvider.execute", reasons)
            self.assertIn("frontend usability evidence does not mention reviewed relationship", reasons)

    def test_runtime_validator_detects_missing_playwright_relationship_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "app/frontend/tests/smoke.e2e.spec.ts",
                'test("generated app loads", async ({ page }) => { await page.goto("/app/"); });\n',
            )

            issues = collect_frontend_runtime_issues(repo_root)
            reasons = "\n".join(issue["reason"] for issue in issues)
            self.assertIn("generated Playwright smoke is missing relationship proof token", reasons)

    def test_runtime_validator_rejects_reference_many_field_tomany_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "app/frontend/src/shared-runtime/resourceRegistry.tsx",
                "\n".join(
                    (
                        "function ShowContent() { return null; }",
                        "function ManyRelationshipTab() { return null; }",
                        "SingleRelationshipTab",
                        "RelatedRecordDialogLink",
                        "<Tabs",
                        "useDataProvider(",
                        "useList(",
                        "<ListContextProvider",
                        "resolveRelationshipExecuteRequest(",
                        "extractExecuteRecords(",
                        "ReferenceManyField",
                    )
                ),
            )

            issues = collect_frontend_runtime_issues(repo_root)
            reasons = "\n".join(issue["reason"] for issue in issues)
            self.assertIn("ReferenceManyField", reasons)

    def test_runtime_validator_rejects_plain_text_show_relationship_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "app/frontend/src/shared-runtime/resourceRegistry.tsx",
                "\n".join(
                    (
                        "ShowContent(",
                        "ManyRelationshipTab(",
                        "SingleRelationshipTab",
                        "RelatedRecordDialogLink",
                        'surface="list"',
                        'surface="summary"',
                        "relationship-tab-panel:tomany:",
                        "relationship-tab-panel:toone:",
                        "data-relationship-fetch-source",
                        "<Tabs",
                        "useDataProvider(",
                        "useList(",
                        "<ListContextProvider",
                        "resolveRelationshipExecuteRequest(",
                        "extractExecuteRecords(",
                        "getRelatedRecordLabel(record, item.relationship, targetMeta)",
                    )
                ),
            )

            issues = collect_frontend_runtime_issues(repo_root)
            reasons = "\n".join(issue["reason"] for issue in issues)
            self.assertIn("plain text instead of RelatedRecordDialogLink", reasons)


if __name__ == "__main__":
    unittest.main()
