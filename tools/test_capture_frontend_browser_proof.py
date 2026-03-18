from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from capture_frontend_browser_proof import (
    has_ui_preview_capture_script,
    read_manifest_capture_status,
    run_script_capture,
)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CaptureFrontendBrowserProofTests(unittest.TestCase):
    def test_detects_ui_preview_capture_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frontend_root = Path(tmp)
            write_file(
                frontend_root / "package.json",
                '{\n  "scripts": {\n    "capture:ui-previews": "playwright test ui-previews.e2e.spec.ts"\n  }\n}\n',
            )

            self.assertTrue(has_ui_preview_capture_script(frontend_root))

    def test_run_script_capture_requires_captured_manifest_and_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frontend_root = Path(tmp) / "frontend"
            screenshots_dir = Path(tmp) / "evidence" / "ui-previews"
            manifest_path = screenshots_dir / "manifest.md"
            frontend_root.mkdir(parents=True, exist_ok=True)
            write_file(
                frontend_root / "package.json",
                '{\n  "scripts": {\n    "capture:ui-previews": "playwright test ui-previews.e2e.spec.ts"\n  }\n}\n',
            )

            def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
                write_file(manifest_path, "# UI Preview Manifest\n\ncapture_status: captured\n")
                write_file(screenshots_dir / "project-overview.png", "fake image")

                class Result:
                    returncode = 0
                    stdout = "ok"
                    stderr = ""

                return Result()

            with patch("capture_frontend_browser_proof.shutil.which", return_value="/usr/bin/npm"):
                with patch("capture_frontend_browser_proof.subprocess.run", side_effect=fake_run):
                    ok, detail = run_script_capture(frontend_root, screenshots_dir, manifest_path)

            self.assertTrue(ok)
            self.assertIn("ok", detail)
            self.assertEqual(read_manifest_capture_status(manifest_path), "captured")

    def test_run_script_capture_rejects_environment_blocked_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frontend_root = Path(tmp) / "frontend"
            screenshots_dir = Path(tmp) / "evidence" / "ui-previews"
            manifest_path = screenshots_dir / "manifest.md"
            frontend_root.mkdir(parents=True, exist_ok=True)
            write_file(
                frontend_root / "package.json",
                '{\n  "scripts": {\n    "capture:ui-previews": "playwright test ui-previews.e2e.spec.ts"\n  }\n}\n',
            )

            def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
                write_file(manifest_path, "# UI Preview Manifest\n\ncapture_status: environment-blocked\n")

                class Result:
                    returncode = 0
                    stdout = "ok"
                    stderr = ""

                return Result()

            with patch("capture_frontend_browser_proof.shutil.which", return_value="/usr/bin/npm"):
                with patch("capture_frontend_browser_proof.subprocess.run", side_effect=fake_run):
                    ok, detail = run_script_capture(frontend_root, screenshots_dir, manifest_path)

            self.assertFalse(ok)
            self.assertIn("capture_status=environment-blocked", detail)

    def test_reads_bulleted_manifest_capture_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.md"
            write_file(
                manifest_path,
                "\n".join(
                    [
                        "# UI Preview Manifest",
                        "",
                        "- capture_status: captured",
                        "- command: npm run capture:ui-previews",
                    ]
                )
                + "\n",
            )

            self.assertEqual(read_manifest_capture_status(manifest_path), "captured")


if __name__ == "__main__":
    unittest.main()
