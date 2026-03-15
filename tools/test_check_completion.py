from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_completion import collect_blockers


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CheckCompletionTests(unittest.TestCase):
    def test_reports_blocked_architect_integration_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/role-state/architect/inbox/blocked.md",
                "\n".join(
                    [
                        "from: frontend",
                        "to: architect",
                        "",
                        "## Gate Status",
                        "- blocked",
                        "",
                        "## Notes",
                        "- integration drift remains unresolved",
                    ]
                ),
            )

            blockers = collect_blockers(repo_root)
            kinds = {blocker["kind"] for blocker in blockers}
            self.assertIn("architect-blocked-integration-work", kinds)

    def test_reports_blocked_required_artifact_and_missing_app_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/architecture/runtime-bom.md",
                "owner: architect\nphase: phase-2-architecture-contract\nstatus: stub\n",
            )
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/architecture/runtime-bom.md",
                "owner: architect\nphase: phase-2-architecture-contract\nstatus: blocked\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )

            blockers = collect_blockers(repo_root)
            kinds = {blocker["kind"] for blocker in blockers}
            paths = {blocker["path"] for blocker in blockers}
            self.assertIn("required-artifact-not-final", kinds)
            self.assertIn("missing-generated-app-output", kinds)
            self.assertIn("runs/current/artifacts/architecture/runtime-bom.md", paths)
            self.assertIn("app/frontend/package.json", paths)

    def test_treats_devops_alias_queue_as_optional_deployment_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/role-state/devops/inbox/work.md",
                "from: architect\nto: devops\n",
            )

            blockers = collect_blockers(repo_root)
            matching = [blocker for blocker in blockers if blocker["kind"] == "optional-deployment-inbox-not-empty"]
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0]["path"], "runs/current/role-state/devops/inbox")


if __name__ == "__main__":
    unittest.main()
