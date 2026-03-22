from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validators.policy.validate_frontend_adapter_contracts import (
    collect_adapter_lane_issues,
    collect_execute_usage_issues,
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


if __name__ == "__main__":
    unittest.main()
