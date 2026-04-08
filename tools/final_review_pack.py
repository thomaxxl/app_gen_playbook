from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

from orchestrator_common import parse_metadata_block, resolve_repo_root


FINAL_REVIEW_ROOT = Path("runs/current/evidence/final")
FINAL_REVIEW_INDEX = FINAL_REVIEW_ROOT / "review-index.md"
FINAL_REVIEW_PLACEHOLDER_MARKER = "starter_status: pending-review-evidence"
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")

FINAL_REVIEW_COPY_FILES: tuple[tuple[str, str, bool, str], ...] = (
    (
        "runs/current/artifacts/product/brief.md",
        "brief.md",
        True,
        "product framing and app purpose",
    ),
    (
        "runs/current/artifacts/product/problem-framing.md",
        "problem-framing.md",
        True,
        "who / why / what / how framing and user pain points",
    ),
    (
        "runs/current/artifacts/product/acceptance-criteria.md",
        "acceptance-criteria.md",
        True,
        "user-facing acceptance target",
    ),
    (
        "runs/current/artifacts/product/user-stories.md",
        "user-stories.md",
        True,
        "current-release scope and testability",
    ),
    (
        "runs/current/artifacts/product/conceptual-domain-model.md",
        "conceptual-domain-model.md",
        True,
        "high-level domain concepts and relationships",
    ),
    (
        "runs/current/artifacts/product/business-rules.md",
        "business-rules.md",
        True,
        "human-readable business-rule catalog",
    ),
    (
        "runs/current/artifacts/product/sample-data.md",
        "sample-data.md",
        True,
        "expected visible data and delivery-seed policy",
    ),
    (
        "runs/current/artifacts/product/acceptance-review.md",
        "acceptance-review.md",
        True,
        "product acceptance decision and story evidence",
    ),
    (
        "runs/current/artifacts/ux/navigation.md",
        "navigation.md",
        True,
        "visible entry points and user navigation",
    ),
    (
        "runs/current/evidence/frontend-usability.md",
        "frontend-usability.md",
        True,
        "user-facing usability review summary",
    ),
    (
        "runs/current/evidence/ui-previews/manifest.md",
        "ui-previews/manifest.md",
        True,
        "reference screenshot manifest",
    ),
    (
        "runs/current/evidence/ui-previews/qa-manifest.md",
        "ui-previews/qa-manifest.md",
        False,
        "final QA screenshot manifest when available",
    ),
)


def _reset_generated_children(final_root: Path) -> None:
    final_root.mkdir(parents=True, exist_ok=True)
    for child in final_root.iterdir():
        if child.name == "README.md":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _iter_image_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return ()
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def ui_preview_capture_status(repo_root: Path) -> str:
    manifest_path = repo_root / "runs/current/evidence/ui-previews/manifest.md"
    if not manifest_path.exists():
        return ""
    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("capture_status:"):
            return stripped.partition(":")[2].strip().lower()
        if stripped.startswith("- capture_status:"):
            return stripped.partition(":")[2].strip().lower()
    return ""


def build_review_index(repo_root: Path) -> str:
    acceptance_review = repo_root / "runs/current/artifacts/product/acceptance-review.md"
    acceptance_status = str(parse_metadata_block(acceptance_review).get("status", "")).strip() or "unknown"
    capture_status = ui_preview_capture_status(repo_root) or "unknown"
    preview_images = [
        path.relative_to(repo_root / FINAL_REVIEW_ROOT).as_posix()
        for path in _iter_image_files(repo_root / FINAL_REVIEW_ROOT / "ui-previews")
    ]

    lines = [
        "---",
        "owner: product_manager",
        "phase: phase-7-product-acceptance",
        "status: ready-for-handoff",
        "last_updated_by: product_manager",
        "---",
        "",
        "# Final Review Pack",
        "",
        "This directory is the no-code audit pack for the delivered app.",
        "It is intended to support a high-level review of the application from a",
        "user and product perspective without opening implementation files.",
        "",
        f"- acceptance_status: {acceptance_status}",
        f"- ui_preview_capture_status: {capture_status}",
        f"- copied_screenshot_count: {len(preview_images)}",
        "",
        "## Included Review Files",
        "",
        "| Final Pack File | Source | Why It Matters |",
        "| --- | --- | --- |",
    ]
    for source_rel, dest_rel, _, purpose in FINAL_REVIEW_COPY_FILES:
        lines.append(f"| `{dest_rel}` | `{source_rel}` | {purpose} |")

    lines.extend(
        [
            "",
            "## Screenshot Coverage",
            "",
            "- `ui-previews/manifest.md` explains whether screenshots were captured,",
            "  not required, or blocked.",
            "- When screenshots were captured, copied images under `ui-previews/` are",
            "  the reference visuals for this audit pack.",
            "",
            "## Audit Guidance",
            "",
            "Use this directory to review:",
            "",
            "- the product promise and acceptance target",
            "- the user-facing scope and workflows",
            "- the high-level data/domain model",
            "- the business-rule intent",
            "- the delivered navigation and visible screenshots",
            "",
            "Treat this pack as the review surface for high-level product evaluation;",
            "do not rely on source-code inspection to understand the app at a user",
            "level.",
            "",
        ]
    )
    return "\n".join(lines)


def compile_final_review_pack(repo_root: Path) -> dict[str, object]:
    repo_root = resolve_repo_root(repo_root)
    final_root = repo_root / FINAL_REVIEW_ROOT
    missing_required_sources: list[str] = []

    for source_rel, _, required, _ in FINAL_REVIEW_COPY_FILES:
        source = repo_root / source_rel
        if not source.exists() and required:
            missing_required_sources.append(source_rel)

    if missing_required_sources:
        raise FileNotFoundError(
            "missing required sources for final review pack: " + ", ".join(missing_required_sources)
        )

    _reset_generated_children(final_root)

    copied_files: list[str] = []

    for source_rel, dest_rel, _, _ in FINAL_REVIEW_COPY_FILES:
        source = repo_root / source_rel
        if not source.exists():
            continue
        destination = final_root / dest_rel
        _copy_file(source, destination)
        copied_files.append(destination.relative_to(repo_root).as_posix())

    preview_root = repo_root / "runs/current/evidence/ui-previews"
    copied_images: list[str] = []
    if preview_root.exists():
        for source in _iter_image_files(preview_root):
            destination = final_root / "ui-previews" / source.relative_to(preview_root)
            _copy_file(source, destination)
            copied_images.append(destination.relative_to(repo_root).as_posix())

    index_path = repo_root / FINAL_REVIEW_INDEX
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(build_review_index(repo_root), encoding="utf-8")
    copied_files.append(index_path.relative_to(repo_root).as_posix())

    return {
        "final_root": final_root.relative_to(repo_root).as_posix(),
        "copied_files": copied_files,
        "copied_images": copied_images,
    }


def collect_final_review_pack_issues(repo_root: Path) -> list[str]:
    repo_root = resolve_repo_root(repo_root)
    final_root = repo_root / FINAL_REVIEW_ROOT
    index_path = repo_root / FINAL_REVIEW_INDEX
    issues: list[str] = []

    if not index_path.exists():
        return ["final review pack index is missing"]

    index_text = index_path.read_text(encoding="utf-8")
    if FINAL_REVIEW_PLACEHOLDER_MARKER in index_text:
        issues.append("final review pack index is still a starter placeholder")

    for source_rel, dest_rel, required, _ in FINAL_REVIEW_COPY_FILES:
        source = repo_root / source_rel
        destination = final_root / dest_rel
        if not source.exists():
            if required:
                issues.append(f"required source for final review pack is missing: {source_rel}")
            continue
        if not destination.exists():
            issues.append(f"final review pack is missing copied file `{dest_rel}`")
            continue
        if source.read_bytes() != destination.read_bytes():
            issues.append(f"final review pack copy `{dest_rel}` is stale relative to `{source_rel}`")

    preview_root = repo_root / "runs/current/evidence/ui-previews"
    if preview_root.exists():
        for source in _iter_image_files(preview_root):
            destination = final_root / "ui-previews" / source.relative_to(preview_root)
            if not destination.exists():
                issues.append(
                    f"final review pack is missing copied screenshot `{destination.relative_to(final_root).as_posix()}`"
                )
                continue
            if source.read_bytes() != destination.read_bytes():
                issues.append(
                    f"final review pack screenshot `{destination.relative_to(final_root).as_posix()}` is stale"
                )

    capture_status = ui_preview_capture_status(repo_root)
    copied_preview_images = list(_iter_image_files(final_root / "ui-previews"))
    if capture_status == "captured" and not copied_preview_images:
        issues.append("ui preview manifest says screenshots were captured, but the final review pack has none")

    return issues
