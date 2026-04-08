from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from final_review_pack import collect_final_review_pack_issues, compile_final_review_pack


def write_file(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


class FinalReviewPackTests(unittest.TestCase):
    def test_compile_final_review_pack_copies_required_files_and_screenshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            for relative in (
                "runs/current/artifacts/product/brief.md",
                "runs/current/artifacts/product/problem-framing.md",
                "runs/current/artifacts/product/acceptance-criteria.md",
                "runs/current/artifacts/product/user-stories.md",
                "runs/current/artifacts/product/conceptual-domain-model.md",
                "runs/current/artifacts/product/business-rules.md",
                "runs/current/artifacts/product/sample-data.md",
                "runs/current/artifacts/product/acceptance-review.md",
                "runs/current/artifacts/ux/navigation.md",
                "runs/current/artifacts/ux/visual-direction.md",
                "runs/current/artifacts/ux/draft-flow-review.md",
                "runs/current/evidence/frontend-usability.md",
            ):
                write_file(repo_root / relative, f"# {Path(relative).name}\n")

            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "---\nowner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n---\n\n# Acceptance\n",
            )
            write_file(
                repo_root / "runs/current/evidence/ui-previews/manifest.md",
                "# UI Preview Manifest\n\ncapture_status: captured\n",
            )
            write_file(
                repo_root / "runs/current/evidence/ui-previews/qa-manifest.md",
                "# QA Manifest\n\ncapture_status: captured\n",
            )
            write_file(repo_root / "runs/current/evidence/ui-previews/overview.png", b"png-a")
            write_file(repo_root / "runs/current/evidence/ui-previews/qa/final.png", b"png-b")
            write_file(repo_root / "runs/current/evidence/final/README.md", "# Final\n")

            payload = compile_final_review_pack(repo_root)

            self.assertEqual(payload["final_root"], "runs/current/evidence/final")
            self.assertTrue((repo_root / "runs/current/evidence/final/review-index.md").exists())
            self.assertEqual(
                (repo_root / "runs/current/evidence/final/business-rules.md").read_text(encoding="utf-8"),
                "# business-rules.md\n",
            )
            self.assertEqual(
                (repo_root / "runs/current/evidence/final/visual-direction.md").read_text(encoding="utf-8"),
                "# visual-direction.md\n",
            )
            self.assertEqual(
                (repo_root / "runs/current/evidence/final/draft-flow-review.md").read_text(encoding="utf-8"),
                "# draft-flow-review.md\n",
            )
            self.assertEqual(
                (repo_root / "runs/current/evidence/final/ui-previews/overview.png").read_bytes(),
                b"png-a",
            )
            self.assertEqual(
                (repo_root / "runs/current/evidence/final/ui-previews/qa/final.png").read_bytes(),
                b"png-b",
            )

    def test_collect_final_review_pack_issues_detects_stale_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(repo_root / "runs/current/artifacts/product/brief.md", "brief v2\n")
            write_file(repo_root / "runs/current/artifacts/product/problem-framing.md", "framing v2\n")
            write_file(repo_root / "runs/current/artifacts/product/acceptance-criteria.md", "ok\n")
            write_file(repo_root / "runs/current/artifacts/product/user-stories.md", "ok\n")
            write_file(repo_root / "runs/current/artifacts/product/conceptual-domain-model.md", "ok\n")
            write_file(repo_root / "runs/current/artifacts/product/business-rules.md", "ok\n")
            write_file(repo_root / "runs/current/artifacts/product/sample-data.md", "ok\n")
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "---\nowner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n---\n",
            )
            write_file(repo_root / "runs/current/artifacts/ux/navigation.md", "ok\n")
            write_file(repo_root / "runs/current/evidence/frontend-usability.md", "ok\n")
            write_file(repo_root / "runs/current/evidence/ui-previews/manifest.md", "capture_status: not-required\n")
            write_file(repo_root / "runs/current/evidence/final/README.md", "# Final\n")
            write_file(
                repo_root / "runs/current/evidence/final/review-index.md",
                "---\nowner: product_manager\nphase: phase-7-product-acceptance\nstatus: ready-for-handoff\n---\n",
            )
            write_file(repo_root / "runs/current/evidence/final/brief.md", "brief v1\n")
            write_file(repo_root / "runs/current/evidence/final/problem-framing.md", "framing v2\n")
            write_file(repo_root / "runs/current/evidence/final/acceptance-criteria.md", "ok\n")
            write_file(repo_root / "runs/current/evidence/final/user-stories.md", "ok\n")
            write_file(repo_root / "runs/current/evidence/final/conceptual-domain-model.md", "ok\n")
            write_file(repo_root / "runs/current/evidence/final/business-rules.md", "ok\n")
            write_file(repo_root / "runs/current/evidence/final/sample-data.md", "ok\n")
            write_file(repo_root / "runs/current/evidence/final/acceptance-review.md", "---\nowner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n---\n")
            write_file(repo_root / "runs/current/evidence/final/navigation.md", "ok\n")
            write_file(repo_root / "runs/current/evidence/final/frontend-usability.md", "ok\n")
            write_file(repo_root / "runs/current/evidence/final/ui-previews/manifest.md", "capture_status: not-required\n")

            issues = collect_final_review_pack_issues(repo_root)
            self.assertTrue(any("brief.md" in issue and "stale" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
