from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from run_dashboard.collector import collect_artifacts, collect_handoffs, collect_run_files, collect_run_snapshot, normalize_role
from run_dashboard.markdown import parse_frontmatter, parse_handoff_message


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class MarkdownParsingTests(unittest.TestCase):
    def test_parse_frontmatter_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "artifact.md"
            write_file(
                path,
                "\n".join(
                    [
                        "---",
                        "owner: frontend",
                        "phase: phase-3-ux-and-interaction-design",
                        "status: ready-for-handoff",
                        "depends_on:",
                        "  - a.md",
                        "  - b.md",
                        "unresolved:",
                        "  - none",
                        "---",
                        "",
                        "# Title",
                    ]
                ),
            )
            parsed = parse_frontmatter(path)
            self.assertEqual(parsed["owner"], "frontend")
            self.assertEqual(parsed["depends_on"], ["a.md", "b.md"])

    def test_parse_handoff_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.md"
            write_file(
                path,
                "\n".join(
                    [
                        "from: architect",
                        "to: devops",
                        "topic: runtime-bom",
                        "",
                        "## Required Reads",
                        "- a.md",
                        "- b.md",
                        "",
                        "## Gate Status",
                        "- blocked",
                    ]
                ),
            )
            parsed = parse_handoff_message(path)
            self.assertEqual(parsed["from"], "architect")
            self.assertEqual(parsed["to"], "devops")
            self.assertEqual(parsed["required reads"], ["a.md", "b.md"])
            self.assertEqual(parsed["gate status"], "blocked")


class CollectorTests(unittest.TestCase):
    def test_collect_handoffs_defaults_importance_to_medium(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_file(
                root / "runs/current/role-state/backend/inbox/msg.md",
                "\n".join(
                    [
                        "from: architect",
                        "to: backend",
                        "",
                        "## Gate Status",
                        "- pass",
                    ]
                ),
            )
            run_files, _, _ = collect_run_files(root, "run-1")
            rows, _ = collect_handoffs(root, "run-1", run_files)
            self.assertEqual(rows[0]["importance"], "medium")
            self.assertFalse(rows[0]["requires_dual_validation"])
            self.assertTrue(rows[0]["dual_validation_complete"])

    def test_collect_handoffs_tracks_high_importance_dual_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_file(
                root / "runs/current/role-state/backend/inbox/msg.md",
                "\n".join(
                    [
                        "from: architect",
                        "to: backend",
                        "importance: high",
                        "validated_by: product_manager, architect",
                        "",
                        "## Gate Status",
                        "- blocked",
                    ]
                ),
            )
            run_files, _, _ = collect_run_files(root, "run-1")
            rows, _ = collect_handoffs(root, "run-1", run_files)
            self.assertEqual(rows[0]["importance"], "high")
            self.assertTrue(rows[0]["requires_dual_validation"])
            self.assertTrue(rows[0]["product_manager_validated"])
            self.assertTrue(rows[0]["architect_validated"])
            self.assertTrue(rows[0]["dual_validation_complete"])

    def test_collect_handoffs_keeps_warning_pending_until_both_validate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_file(
                root / "runs/current/role-state/backend/inbox/msg.md",
                "\n".join(
                    [
                        "from: architect",
                        "to: backend",
                        "importance: warning",
                        "product_manager_validated: true",
                        "",
                        "## Gate Status",
                        "- blocked",
                    ]
                ),
            )
            run_files, _, _ = collect_run_files(root, "run-1")
            rows, _ = collect_handoffs(root, "run-1", run_files)
            self.assertEqual(rows[0]["importance"], "warning")
            self.assertTrue(rows[0]["requires_dual_validation"])
            self.assertTrue(rows[0]["product_manager_validated"])
            self.assertFalse(rows[0]["architect_validated"])
            self.assertFalse(rows[0]["dual_validation_complete"])

    def test_collect_handoffs_normalizes_devops_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_file(
                root / "runs/current/role-state/devops/inbox/msg.md",
                "\n".join(
                    [
                        "from: architect",
                        "to: devops",
                        "",
                        "## Gate Status",
                        "- blocked",
                    ]
                ),
            )
            run_files, _, _ = collect_run_files(root, "run-1")
            rows, relationships = collect_handoffs(root, "run-1", run_files)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["to_role_code"], "devops")
            self.assertEqual(rows[0]["message_state"], "inbox")
            self.assertEqual(rows[0]["path"], "runs/current/role-state/devops/inbox/msg.md")
            self.assertTrue(any(rel["relation_type"] == "blocking_issue_ref" for rel in relationships) is False)

    def test_collect_handoffs_preserves_duplicate_states_by_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "\n".join(
                [
                    "from: architect",
                    "to: backend",
                ]
            )
            write_file(root / "runs/current/role-state/backend/inbox/msg.md", content)
            write_file(root / "runs/current/role-state/backend/processed/msg.md", content)
            run_files, _, _ = collect_run_files(root, "run-1")
            rows, _ = collect_handoffs(root, "run-1", run_files)
            self.assertEqual(len(rows), 2)
            self.assertEqual({row["state_dir"] for row in rows}, {"inbox", "processed"})
            self.assertEqual(len({row["id"] for row in rows}), 2)

    def test_collect_artifacts_recurses_into_family_subdirectories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_file(
                root / "runs/current/artifacts/ux/nested/navigation.md",
                "\n".join(
                    [
                        "---",
                        "owner: frontend",
                        "phase: phase-3-ux-and-interaction-design",
                        "status: ready-for-handoff",
                        "---",
                        "",
                        "# Navigation",
                    ]
                ),
            )
            run_files, markdown_documents, _ = collect_run_files(root, "run-1")
            packages, artifacts, dependencies, relationships = collect_artifacts(root, "run-1", run_files, markdown_documents)
            self.assertEqual(len(packages), 1)
            self.assertEqual(packages[0]["family"], "ux")
            self.assertEqual(packages[0]["overall_status"], "ready_for_handoff")
            self.assertEqual(len(artifacts), 1)
            self.assertTrue(artifacts[0]["path"].endswith("runs/current/artifacts/ux/nested/navigation.md"))
            self.assertEqual(dependencies, [])
            self.assertEqual(relationships, [])

    def test_normalize_role(self) -> None:
        self.assertEqual(normalize_role("deployment"), "devops")
        self.assertEqual(normalize_role("devops"), "devops")
        self.assertEqual(normalize_role("backend"), "backend")

    def test_collect_run_snapshot_includes_product_scope_entities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_file(
                root / "runs/current/orchestrator/run-status.json",
                json.dumps(
                    {
                        "run_id": "RUN-TEST",
                        "mode": "iterative-change-run",
                        "status": "active",
                        "change_id": "CR-TEST",
                        "started_at": "2026-04-07T09:00:00Z",
                    }
                )
                + "\n",
            )
            (root / "runs/current/facts").mkdir(parents=True, exist_ok=True)
            write_file(
                root / "runs/current/facts/product-scope.json",
                json.dumps(
                    {
                        "ok": True,
                        "issues": [],
                        "product_scope": {
                            "source_paths": [
                                "runs/current/artifacts/product/user-stories.md",
                                "runs/current/artifacts/product/traceability-matrix.md",
                            ],
                            "story_index": [
                                {
                                    "story_id": "US-001",
                                    "title": "Current run orientation",
                                    "actor": "Operator",
                                    "priority": "P1",
                                    "delivery_class": "must",
                                    "release": "R1",
                                    "story_type": "reporting-search",
                                    "story_statement": "As an operator, I understand the current run quickly.",
                                    "why_priority": "It is the first view.",
                                    "independent_test": "Open overview and confirm orientation.",
                                    "current_release": True,
                                    "acceptance_scenario_count": 1,
                                    "edge_case_count": 1,
                                }
                            ],
                            "story_detail_index": [
                                {
                                    "story_id": "US-001",
                                    "source_anchor": "US-001",
                                    "section_keys": ["Acceptance Scenarios", "Edge Cases"],
                                    "acceptance_scenarios": ["Given the run is active When the user opens overview Then the current run is visible."],
                                    "edge_cases": ["No current run exists."],
                                    "detail_sections": {
                                        "Acceptance Scenarios": "Given ...",
                                        "Edge Cases": "- none",
                                    },
                                }
                            ],
                            "traceability_rows": [
                                {
                                    "story_id": "US-001",
                                    "workflow_ids": ["WF-001"],
                                    "rule_ids": ["BR-001"],
                                    "resource_ids": ["Run"],
                                    "page_ids": ["PAGE-001"],
                                    "route_ids": ["N001"],
                                    "sample_data_ids": ["SD-001"],
                                    "acceptance_ids": ["AC-001"],
                                    "permission_context": "operator read access",
                                    "preview_required": True,
                                    "qa_live_required": True,
                                    "acceptance_owner": "product_manager",
                                    "primary_evidence_mode": "ui",
                                }
                            ],
                        },
                    }
                )
                + "\n",
            )
            write_file(
                root / "runs/current/facts/business-rules.json",
                json.dumps(
                    {
                        "ok": True,
                        "issues": [],
                        "business_rules": {
                            "source_paths": [
                                "runs/current/artifacts/product/business-rules.md",
                                "runs/current/artifacts/product/traceability-matrix.md",
                            ],
                            "rules": [
                                {
                                    "rule_id": "BR-001",
                                    "title": "Current run pinned by default",
                                    "rule_class": "presentation",
                                    "status": "approved",
                                    "plain_language_rule": "The dashboard opens on the current run.",
                                    "rationale": "Current-run first orientation.",
                                    "source": "brief",
                                    "trigger": "overview render",
                                    "preconditions": "current run exists",
                                    "applies_to": ["Overview"],
                                    "valid_outcome": "Current run is visible.",
                                    "invalid_outcome": "History opens first.",
                                    "user_visible_consequence": "Operator is oriented immediately.",
                                    "backend_enforcement": "required",
                                    "frontend_mirror": "async",
                                    "frontend_mirror_reason": "UI mirrors the observer data.",
                                    "authoritative_error_message": "Current run context is unavailable.",
                                    "examples": {"valid": ["Current run card appears first."], "invalid": ["History is shown by default."]},
                                    "backend_test_required": True,
                                    "frontend_test_required": True,
                                    "traceability_story_ids": ["US-001"],
                                    "source_anchor": "BR-001",
                                }
                            ],
                            "rule_index": [
                                {
                                    "rule_id": "BR-001",
                                    "title": "Current run pinned by default",
                                    "rule_class": "presentation",
                                    "frontend_mirror": "async",
                                    "status": "approved",
                                    "source_anchor": "BR-001",
                                }
                            ],
                        },
                    }
                )
                + "\n",
            )
            for relpath in (
                "runs/current/artifacts/product/user-stories.md",
                "runs/current/artifacts/product/traceability-matrix.md",
                "runs/current/artifacts/product/business-rules.md",
                "runs/current/input.md",
            ):
                write_file(root / relpath, f"# {Path(relpath).name}\n")

            def fake_run_tool_json(_root: Path, tool_relative_path: str, _args: list[str]) -> dict[str, object]:
                if tool_relative_path == "tools/status_report.py":
                    return {
                        "generated_at": "2026-04-07T09:00:00Z",
                        "current_phase": {"key": "phase-1-product-definition", "label": "Product Definition"},
                        "current_phase_code": "phase-1-product-definition",
                        "overall_progress": 12.5,
                        "roles": {},
                        "artifact_areas": {},
                        "artifacts": {},
                        "completion": {"complete": False, "blockers": []},
                        "phases": {},
                        "phase5_ready": False,
                        "phase5_blockers": [],
                        "evidence": {},
                        "liveness": {},
                    }
                if tool_relative_path == "tools/check_completion.py":
                    return {"complete": False, "blockers": []}
                raise AssertionError(tool_relative_path)

            from unittest.mock import patch

            with patch("run_dashboard.collector.run_tool_json", side_effect=fake_run_tool_json):
                snapshot = collect_run_snapshot(root, "app_gen_playbook", "App Gen Playbook")

            self.assertEqual(len(snapshot["user_stories"]), 1)
            self.assertEqual(snapshot["user_stories"][0]["story_id"], "US-001")
            self.assertEqual(snapshot["user_story_traceability"][0]["rule_ids_json"], ["BR-001"])
            self.assertEqual(len(snapshot["business_rules"]), 1)
            self.assertEqual(snapshot["business_rules"][0]["rule_id"], "BR-001")
            self.assertEqual(snapshot["business_rule_examples"][0]["example_kind"], "valid")
            self.assertEqual(snapshot["business_rule_story_links"][0]["story_id"], "US-001")


if __name__ == "__main__":
    unittest.main()
