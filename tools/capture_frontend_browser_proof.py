#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

CAPTURE_TIMEOUT_SECONDS = 30
SCRIPT_CAPTURE_TIMEOUT_SECONDS = 180
CAPTURE_SETTLE_MILLISECONDS = 1000


DEFAULT_ROUTES = (
    ("admin-entry", "/admin-app/"),
)
MARKDOWN_CAPTURE_STATUS_PATTERN = re.compile(
    r"(?im)^(?:-\s*)?capture_status:\s*([a-z0-9_-]+)\s*$"
)


def normalize_url(base_url: str, route: str) -> str:
    if route.startswith(("http://", "https://", "data:")):
        return route
    if route.startswith("/"):
        if base_url.endswith("/"):
            return f"{base_url.rstrip('/')}{route}"
        origin = base_url.split("/admin", 1)[0].rstrip("/")
        return f"{origin}{route}"
    return f"{base_url.rstrip('/')}/{route.lstrip('/')}"


def package_json_scripts(frontend_root: Path) -> dict[str, str]:
    package_json_path = frontend_root / "package.json"
    if not package_json_path.exists():
        return {}
    try:
        payload = json.loads(package_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    scripts = payload.get("scripts")
    if not isinstance(scripts, dict):
        return {}
    return {str(key): str(value) for key, value in scripts.items()}


def has_ui_preview_capture_script(frontend_root: Path) -> bool:
    return "capture:ui-previews" in package_json_scripts(frontend_root)


def read_manifest_capture_status(manifest_path: Path) -> str:
    if not manifest_path.exists():
        return ""
    text = manifest_path.read_text(encoding="utf-8")
    match = MARKDOWN_CAPTURE_STATUS_PATTERN.search(text)
    if match is None:
        return ""
    return match.group(1).strip().lower()


def reviewable_image_files(screenshots_dir: Path) -> list[Path]:
    if not screenshots_dir.exists():
        return []
    return sorted(
        path
        for path in screenshots_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )


def run_script_capture(frontend_root: Path, screenshots_dir: Path, manifest_path: Path) -> tuple[bool, str]:
    npm_path = shutil.which("npm")
    if npm_path is None:
        return False, "npm is not available in PATH"

    screenshots_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["UI_PREVIEW_OUTPUT_DIR"] = str(screenshots_dir)

    try:
        proc = subprocess.run(
            [npm_path, "run", "capture:ui-previews"],
            cwd=frontend_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=SCRIPT_CAPTURE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        if detail:
            return False, f"timed out after {SCRIPT_CAPTURE_TIMEOUT_SECONDS}s: {detail}"
        return False, f"timed out after {SCRIPT_CAPTURE_TIMEOUT_SECONDS}s"

    detail = (proc.stderr or proc.stdout).strip()
    capture_state = read_manifest_capture_status(manifest_path)
    images = reviewable_image_files(screenshots_dir)
    if proc.returncode == 0 and capture_state == "captured" and images:
        return True, detail or "captured ui previews via npm run capture:ui-previews"

    if proc.returncode == 0 and capture_state != "captured":
        message = f"capture script finished but manifest reported capture_status={capture_state or 'missing'}"
        if detail:
            message = f"{message}: {detail}"
        return False, message
    if proc.returncode == 0 and not images:
        return False, detail or "capture script finished but did not write reviewable image files"
    return False, detail or "npm run capture:ui-previews failed"


def run_capture(frontend_root: Path, url: str, output_path: Path) -> tuple[bool, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    script = f"""
import {{ chromium }} from "playwright";

const [url, outputPath] = process.argv.slice(1);
const browser = await chromium.launch({{ headless: true }});
const page = await browser.newPage();

try {{
  await page.goto(url, {{ waitUntil: "domcontentloaded", timeout: {CAPTURE_TIMEOUT_SECONDS * 1000} }});
  await page.waitForTimeout({CAPTURE_SETTLE_MILLISECONDS});
  await page.screenshot({{ path: outputPath, fullPage: true }});
  const title = await page.title();
  console.log(`captured ${{outputPath}} title=${{title}}`);
}} finally {{
  await browser.close();
}}
""".strip()
    try:
        proc = subprocess.run(
            [
                "node",
                "--input-type=module",
                "-e",
                script,
                url,
                str(output_path),
            ],
            cwd=frontend_root,
            capture_output=True,
            text=True,
            timeout=CAPTURE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        if detail:
            return False, f"timed out after {CAPTURE_TIMEOUT_SECONDS}s: {detail}"
        return False, f"timed out after {CAPTURE_TIMEOUT_SECONDS}s"
    detail = (proc.stderr or proc.stdout).strip()
    if proc.returncode == 0 and output_path.exists():
        return True, detail or f"captured {output_path.name}"
    return False, detail or "playwright screenshot failed"


def write_manifest(manifest_path: Path, status: str, command: str, captured: list[tuple[str, str, str]], failures: list[tuple[str, str, str]]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# UI Preview Manifest",
        "",
        f"capture_status: {status}",
        f"command: {command}",
    ]
    if captured:
        lines.extend(["", "captured_routes:"])
        for label, url, filename in captured:
            lines.append(f"- {label}: {url}")
            lines.append(f"  file: {filename}")
    if failures:
        lines.extend(["", "capture_failures:"])
        for label, url, detail in failures:
            lines.append(f"- {label}: {url}")
            lines.append(f"  detail: {detail}")
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_browser_proof(
    output_path: Path,
    status: str,
    base_url: str,
    captured: list[tuple[str, str, str]],
    failures: list[tuple[str, str, str]],
    manifest_path: Path,
    command: str,
    preview_files: list[str] | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "owner: architect",
        "phase: phase-6-integration-review",
        f"status: {'ready-for-handoff' if status == 'captured' else 'blocked'}",
        "last_updated_by: architect",
        "---",
        "",
        "# Frontend Browser Proof",
        "",
        f"- base_url: {base_url}",
        f"- capture_command: {command}",
        f"- capture_status: {status}",
        f"- ui_preview_manifest: {manifest_path}",
    ]
    if captured:
        lines.extend(["", "## Captured Routes"])
        for label, url, filename in captured:
            lines.append(f"- `{label}`: {url}")
            lines.append(f"  - screenshot: {filename}")
    if failures:
        lines.extend(["", "## Capture Failures"])
        for label, url, detail in failures:
            lines.append(f"- `{label}`: {url}")
            lines.append(f"  - detail: {detail}")
    if preview_files:
        lines.extend(["", "## Captured Preview Files"])
        for preview_file in preview_files:
            lines.append(f"- `{preview_file}`")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:5173")
    parser.add_argument("--route", action="append", default=[])
    parser.add_argument("--output", default="runs/current/evidence/frontend-browser-proof.md")
    parser.add_argument("--manifest", default="runs/current/evidence/ui-previews/manifest.md")
    parser.add_argument("--screenshots-dir", default="runs/current/evidence/ui-previews")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    frontend_root = repo_root / "app" / "frontend"
    output_path = repo_root / args.output
    manifest_path = repo_root / args.manifest
    screenshots_dir = repo_root / args.screenshots_dir

    if has_ui_preview_capture_script(frontend_root):
        command = "npm run capture:ui-previews"
        ok, detail = run_script_capture(frontend_root, screenshots_dir, manifest_path)
        preview_files = [path.name for path in reviewable_image_files(screenshots_dir)]
        status = read_manifest_capture_status(manifest_path) or ("captured" if ok else "environment-blocked")
        write_browser_proof(
            output_path,
            status,
            args.base_url,
            [],
            [] if ok else [("ui-previews-script", args.base_url, detail)],
            manifest_path.relative_to(repo_root).as_posix(),
            command,
            preview_files=preview_files,
        )
        return 0 if ok else 1

    routes: list[tuple[str, str]] = list(DEFAULT_ROUTES)
    for item in args.route:
        if "=" in item:
            label, route = item.split("=", 1)
        else:
            label = f"route-{len(routes) + 1}"
            route = item
        routes.append((label, route))

    command = "node --input-type=module -e <playwright_capture_script> <url> <file>"
    captured: list[tuple[str, str, str]] = []
    failures: list[tuple[str, str, str]] = []

    for label, route in routes:
        url = normalize_url(args.base_url, route)
        filename = f"{label}.png"
        ok, detail = run_capture(frontend_root, url, screenshots_dir / filename)
        if ok:
            captured.append((label, url, filename))
        else:
            failures.append((label, url, detail))

    status = "captured" if captured and not failures else "environment-blocked"
    write_manifest(manifest_path, status, command, captured, failures)
    write_browser_proof(
        output_path,
        status,
        args.base_url,
        captured,
        failures,
        manifest_path.relative_to(repo_root).as_posix(),
        command,
        preview_files=[filename for _, _, filename in captured],
    )
    return 0 if status == "captured" else 1


if __name__ == "__main__":
    raise SystemExit(main())
