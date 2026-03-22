#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from coverage.common import (  # type: ignore[import-not-found]
        normalized_repo_root,
        parse_page_id,
        parse_markdown_table,
        parse_primary_cta_targets,
        read_text,
        story_rows,
        traceability_rows,
        write_json,
    )
else:
    from .common import (
        normalized_repo_root,
        parse_page_id,
        parse_markdown_table,
        parse_primary_cta_targets,
        read_text,
        story_rows,
        traceability_rows,
        write_json,
    )


STORY_BULLET_RE = re.compile(r"(?m)^-\s*`(US-\d+)`\b")
CUSTOM_PAGE_SECTION_RE = re.compile(r"(?m)^##\s+`?(CP-\d+)`?\s+(.+?)\s*$")
PAGE_CATALOG_ITEM_RE = re.compile(r"(?m)^-\s*`((?:CP|RP)-\d+)`\s+(.+?)\s*$")
ROUTE_CATALOG_ITEM_RE = re.compile(r"(?m)^-\s*`(R-\d+)`\s+(.+?)\s*$")
BACKTICK_TOKEN_RE = re.compile(r"`([^`]+)`")

ROUTE_PATH_OVERRIDES = {
    "R-001": "/app/#/Home",
    "R-002": "/app/#/orders/workbench",
    "R-003": "/app/#/orders/credit-attention",
    "R-004": "/app/#/workforce/assignments",
    "R-005": "/app/#/Customer",
    "R-006": "/app/#/Order",
    "R-007": "/app/#/OrderDetail",
    "R-008": "/app/#/Product",
    "R-009": "/app/#/Category",
    "R-010": "/app/#/Supplier",
    "R-011": "/app/#/Shipper",
    "R-012": "/app/#/Employee",
    "R-013": "/app/#/Department",
    "R-014": "/app/#/Territory",
    "R-015": "/app/#/EmployeeTerritory",
    "R-016": "/app/#/Union",
    "R-017": "/app/#/EmployeeAudit",
    "R-018": "/app/#/ProductDetails_View",
}


def _normalize_catalog_label(value: str) -> str:
    normalized = value.strip().lower()
    for needle in (
        "landing route family",
        "route family",
        "resource screens",
        "resource route",
        "contextual review screens",
        "contextual review route",
        "read-only review screens",
        "read-only review route",
        "page",
    ):
        normalized = normalized.replace(needle, "")
    return " ".join(normalized.split())


def _story_rows_for_scope(repo_root: Path) -> list[dict[str, str]]:
    rows = story_rows(repo_root)
    if rows:
        return rows

    text = read_text(repo_root / "runs" / "current" / "artifacts" / "product" / "user-stories.md")
    return [{"Story ID": story_id, "Priority": "must"} for story_id in STORY_BULLET_RE.findall(text)]


def _custom_page_rows_for_scope(path: Path) -> list[dict[str, str]]:
    rows = parse_markdown_table(path)
    if rows:
        return rows

    text = read_text(path)
    return [
        {"Page ID": match.group(1), "Label": match.group(2).strip()}
        for match in CUSTOM_PAGE_SECTION_RE.finditer(text)
    ]


def _catalog_map(text: str, pattern: re.Pattern[str]) -> dict[str, str]:
    return {match.group(1): match.group(2).strip() for match in pattern.finditer(text)}


def _page_to_route_map(page_catalog: dict[str, str], route_catalog: dict[str, str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for page_id, page_label in page_catalog.items():
        normalized_page = _normalize_catalog_label(page_label)
        for route_id, route_label in route_catalog.items():
            normalized_route = _normalize_catalog_label(route_label)
            if normalized_page and normalized_route and (
                normalized_page in normalized_route or normalized_route in normalized_page
            ):
                mapping[page_id] = route_id
                break
    return mapping


def _narrative_navigation_rows(
    repo_root: Path,
    navigation_path: Path,
    custom_pages: list[dict[str, str]],
) -> list[dict[str, str]]:
    text = read_text(navigation_path)
    if not text:
        return []

    traceability_text = read_text(repo_root / "runs" / "current" / "artifacts" / "product" / "traceability-matrix.md")
    page_catalog = _catalog_map(traceability_text, PAGE_CATALOG_ITEM_RE)
    route_catalog = _catalog_map(traceability_text, ROUTE_CATALOG_ITEM_RE)
    page_to_route = _page_to_route_map(page_catalog, route_catalog)
    visible_page_ids = {
        row.get("Page ID", "").strip()
        for row in custom_pages
        if row.get("Page ID", "").strip().startswith("CP-")
    }

    tokens = {token.strip().lower() for token in BACKTICK_TOKEN_RE.findall(text)}
    for page_id, label in page_catalog.items():
        normalized_label = _normalize_catalog_label(label)
        if not normalized_label:
            continue
        for token in tokens:
            if token in normalized_label or normalized_label in token:
                visible_page_ids.add(page_id)
                break

    rows: list[dict[str, str]] = []
    seen_route_ids: set[str] = set()
    for page_id in sorted(visible_page_ids):
        route_id = page_to_route.get(page_id, "").strip()
        if not route_id or route_id in seen_route_ids:
            continue
        path = ROUTE_PATH_OVERRIDES.get(route_id, "")
        if not path:
            continue
        label = route_catalog.get(route_id, page_catalog.get(page_id, route_id)).strip()
        rows.append(
            {
                "Route ID": route_id,
                "Path": path,
                "Label": label,
                "Visibility": "visible",
                "Implementation": "custom" if page_id.startswith("CP-") else "resource",
            }
        )
        seen_route_ids.add(route_id)
    return rows


def _active_change_id(repo_root: Path) -> str:
    run_status_path = repo_root / "runs" / "current" / "orchestrator" / "run-status.json"
    if not run_status_path.exists():
        return ""
    try:
        payload = json.loads(run_status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    return str(payload.get("change_id", "")).strip()


def _preferred_scope_artifact_path(repo_root: Path, artifact_area: str, filename: str) -> Path:
    baseline_path = repo_root / "runs" / "current" / "artifacts" / artifact_area / filename
    change_id = _active_change_id(repo_root)
    if not change_id:
        return baseline_path
    candidate_path = (
        repo_root
        / "runs"
        / "current"
        / "changes"
        / change_id
        / "candidate"
        / "artifacts"
        / artifact_area
        / filename
    )
    if candidate_path.exists():
        return candidate_path
    return baseline_path


def _normalize_route_path(path: str) -> str:
    value = path.strip().strip("`")
    if not value:
        return value
    if value.startswith("/app/#/"):
        return value
    if value.startswith("/#/"):
        return f"/app{value}"
    return value


def compile_product_scope_payload(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    stories = _story_rows_for_scope(repo_root)
    traceability = traceability_rows(repo_root)
    custom_pages_path = _preferred_scope_artifact_path(repo_root, "product", "custom-pages.md")
    navigation_path = _preferred_scope_artifact_path(repo_root, "ux", "navigation.md")
    landing_strategy_path = _preferred_scope_artifact_path(repo_root, "ux", "landing-strategy.md")
    change_scope_active = any(
        "/runs/current/changes/" in path.as_posix()
        for path in (custom_pages_path, navigation_path, landing_strategy_path)
    )
    custom_pages = _custom_page_rows_for_scope(custom_pages_path)
    navigation = parse_markdown_table(navigation_path) or _narrative_navigation_rows(
        repo_root,
        navigation_path,
        custom_pages,
    )

    if not stories:
        issues.append("missing or empty runs/current/artifacts/product/user-stories.md")
    if not traceability:
        issues.append("missing or empty runs/current/artifacts/product/traceability-matrix.md")
    if not navigation:
        issues.append(f"missing or empty {navigation_path.relative_to(repo_root).as_posix()}")
    if not custom_pages:
        issues.append(f"missing or empty {custom_pages_path.relative_to(repo_root).as_posix()}")

    page_ids = {parse_page_id(row.get("Page ID", "")) for row in custom_pages if row.get("Page ID")}
    visible_routes: list[dict[str, str]] = []
    route_ids: set[str] = set()
    for row in navigation:
        visibility = row.get("Visibility", "").strip().lower()
        route_id = row.get("Route ID", "").strip()
        path = _normalize_route_path(row.get("Path", ""))
        if not route_id or not path:
            continue
        route_ids.add(route_id)
        if visibility == "visible":
            visible_routes.append(
                {
                    "route_id": route_id,
                    "path": path,
                    "page_label": row.get("Label", "").strip(),
                    "implementation": row.get("Implementation", "").strip().lower(),
                }
            )

    trace_rows: list[dict[str, Any]] = []
    trace_by_story: dict[str, dict[str, Any]] = {}
    for row in traceability:
        story_id = row.get("Story ID", "").strip()
        if not story_id:
            continue
        page_values = [value.strip() for value in row.get("Page IDs", "").split(",") if value.strip()]
        route_values = [value.strip() for value in row.get("Route IDs", "").split(",") if value.strip()]
        trace_row = {
            "story_id": story_id,
            "priority": row.get("Priority", "").strip().lower(),
            "workflow_ids": [value.strip() for value in row.get("Workflow IDs", "").split(",") if value.strip()],
            "page_ids": page_values,
            "route_ids": route_values,
            "preview_required": row.get("Required preview evidence", "").strip().lower() == "yes",
            "qa_live_required": row.get("Required live QA evidence", "").strip().lower() == "yes",
        }
        trace_rows.append(trace_row)
        trace_by_story[story_id] = trace_row

    must_story_rows: list[dict[str, str]] = []
    for row in stories:
        story_id = row.get("Story ID", "").strip()
        priority = row.get("Priority", "").strip().lower()
        if not story_id or priority != "must":
            continue
        must_story_rows.append(row)
        if story_id not in trace_by_story:
            issues.append(f"{story_id}: missing traceability row")
            continue
        trace_row = trace_by_story[story_id]
        if not trace_row["workflow_ids"]:
            issues.append(f"{story_id}: no workflow mapping in traceability matrix")
        if not trace_row["page_ids"]:
            issues.append(f"{story_id}: no page mapping in traceability matrix")
        if not trace_row["route_ids"]:
            issues.append(f"{story_id}: no route mapping in traceability matrix")
        if change_scope_active:
            continue
        for page_id in trace_row["page_ids"]:
            if page_id not in page_ids:
                issues.append(f"{story_id}: unknown page id {page_id} in traceability matrix")
        for route_id in trace_row["route_ids"]:
            if route_id not in route_ids:
                issues.append(f"{story_id}: unknown route id {route_id} in traceability matrix")

    primary_targets = parse_primary_cta_targets(read_text(landing_strategy_path))
    requires_static_home_cta = any(route["path"] == "/app/#/Home" for route in visible_routes)
    if requires_static_home_cta and not primary_targets:
        issues.append(
            f"{landing_strategy_path.relative_to(repo_root).as_posix()} is missing Primary CTA route target entries"
        )

    payload = {
        "must_stories": [
            {
                "story_id": row.get("Story ID", "").strip(),
                "workflow_ids": trace_by_story.get(row.get("Story ID", "").strip(), {}).get("workflow_ids", []),
                "page_ids": trace_by_story.get(row.get("Story ID", "").strip(), {}).get("page_ids", []),
                "route_ids": trace_by_story.get(row.get("Story ID", "").strip(), {}).get("route_ids", []),
            }
            for row in must_story_rows
        ],
        "required_visible_routes": visible_routes,
        "allowed_home_primary_cta_targets": primary_targets,
        "required_custom_pages": sorted(page_ids),
        "traceability_rows": trace_rows,
        "source_paths": [
            "runs/current/artifacts/product/user-stories.md",
            "runs/current/artifacts/product/traceability-matrix.md",
            custom_pages_path.relative_to(repo_root).as_posix(),
            navigation_path.relative_to(repo_root).as_posix(),
            landing_strategy_path.relative_to(repo_root).as_posix(),
        ],
    }
    return payload, issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    payload, issues = compile_product_scope_payload(repo_root)
    result = {"ok": not issues, "issues": issues, "scope": payload}
    if args.output:
        write_json(Path(args.output), result)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
