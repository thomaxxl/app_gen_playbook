from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from routing_resolver import (
    collect_packet_health_issues,
    parse_yaml_subset,
    resolve_forbidden_paths,
    resolve_read_packet,
    resolve_writable_paths,
)
from validate_role_diff import is_allowed_change


class RoutingResolverTests(unittest.TestCase):
    def write(self, root: Path, relative_path: str, content: str) -> None:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def build_repo(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        repo_root = Path(temp_dir.name)

        self.write(repo_root, ".git", "")
        self.write(
            repo_root,
            "playbook/routing/execution-scopes.yaml",
            "\n".join(
                [
                    "fullstack:",
                    "  active_roles:",
                    "    - product_manager",
                    "    - architect",
                    "    - frontend",
                    "    - backend",
                    "  iterative-change-run:",
                    "    active_phases:",
                    "      - phase-I1-change-intake-and-triage",
                    "      - phase-I2-product-and-scope-delta",
                    "      - phase-I3-architecture-and-contract-delta",
                    "      - phase-I4-frontend-design-delta",
                    "      - phase-I5-frontend-implementation-delta",
                    "      - phase-I6-integration-and-regression-review",
                    "      - phase-I7-change-acceptance",
                    "frontend-only:",
                    "  active_roles:",
                    "    - product_manager",
                    "    - architect",
                    "    - frontend",
                    "  iterative-change-run:",
                    "    active_phases:",
                    "      - phase-I1-change-intake-and-triage",
                    "      - phase-I2-product-and-scope-delta",
                    "      - phase-I3-architecture-and-contract-delta",
                    "      - phase-I4-frontend-design-delta",
                    "      - phase-I5-frontend-implementation-delta",
                    "      - phase-I6-integration-and-regression-review",
                    "      - phase-I7-change-acceptance",
                ]
            )
            + "\n",
        )
        self.write(
            repo_root,
            "playbook/routing/role-core.yaml",
            "\n".join(
                [
                    "frontend:",
                    "  always_load:",
                    "    - playbook/summaries/global-core.md",
                    "  writable:",
                    "    - runs/current/remarks.md",
                    "    - runs/current/role-state/frontend/**",
                    "    - runs/current/artifacts/ux/**",
                    "    - runs/current/changes/*/candidate/artifacts/ux/**",
                    "    - runs/current/changes/*/verification/**",
                    "    - app/frontend/**",
                    "  cannot_write:",
                    "    - app/backend/**",
                    "",
                    "backend:",
                    "  always_load:",
                    "    - playbook/summaries/global-core.md",
                    "  writable:",
                    "    - runs/current/remarks.md",
                    "    - runs/current/role-state/backend/**",
                    "    - runs/current/changes/*/candidate/artifacts/backend-design/**",
                    "    - runs/current/changes/*/verification/**",
                    "    - app/backend/**",
                    "    - app/rules/**",
                    "  cannot_write:",
                    "    - app/frontend/**",
                    "",
                    "architect:",
                    "  always_load:",
                    "    - playbook/summaries/global-core.md",
                    "  writable:",
                    "    - app/**",
                    "  cannot_write:",
                    "    - app/backend/**",
                ]
            )
            + "\n",
        )
        self.write(repo_root, "playbook/routing/phase-bundles.yaml", "")
        self.write(repo_root, "playbook/routing/capability-map.yaml", "")
        self.write(
            repo_root,
            "playbook/task-bundles/frontend-implementation.yaml",
            "\n".join(
                [
                    "name: frontend-implementation",
                    "role: frontend",
                    "always_load:",
                    "  - playbook/process/read-sets/frontend-implementation-core.md",
                    "required_phase:",
                    "  - playbook/process/phases/phase-I5-implementation-delta.md",
                    "required_artifacts:",
                    "  - runs/current/artifacts/ux/navigation.md",
                    "  - runs/current/artifacts/backend-design/model-design.md",
                    "required_candidate_artifacts:",
                    "  - runs/current/changes/*/candidate/artifacts/ux/**",
                    "writable_targets:",
                    "  - app/frontend/**",
                    "  - runs/current/artifacts/ux/**",
                    "  - runs/current/changes/*/candidate/artifacts/ux/**",
                    "  - runs/current/changes/*/verification/**",
                ]
            )
            + "\n",
        )
        self.write(
            repo_root,
            "playbook/task-bundles/change-backend-implementation.yaml",
            "\n".join(
                [
                    "name: change-backend-implementation",
                    "role: backend",
                    "always_load:",
                    "  - playbook/summaries/global-core.md",
                    "required_phase:",
                    "  - playbook/process/phases/phase-I5-implementation-delta.md",
                    "writable_targets:",
                    "  - runs/current/changes/*/verification/**",
                    "  - app/backend/**",
                    "  - app/rules/**",
                ]
            )
            + "\n",
        )
        self.write(repo_root, "runs/current/artifacts/architecture/capability-profile.md", "# Capability Profile\n")
        self.write(repo_root, "runs/current/artifacts/architecture/load-plan.md", "# Load Plan\n")
        self.write(
            repo_root,
            "runs/current/orchestrator/run-status.json",
            "\n".join(
                [
                    "{",
                    '  "change_id": "CR-1",',
                    '  "current_phase": "phase-I5-implementation-delta",',
                    '  "mode": "iterative-change-run"',
                    "}",
                ]
            )
            + "\n",
        )
        self.write(repo_root, "runs/current/changes/CR-1/request.md", "# Request\n")
        self.write(
            repo_root,
            "runs/current/changes/CR-1/classification.yaml",
            "\n".join(
                [
                    "kind: change",
                    "scope_profile: frontend-only",
                    "active_roles:",
                    "  - product_manager",
                    "  - architect",
                    "  - frontend",
                    "active_phases:",
                    "  - phase-I1-change-intake-and-triage",
                    "  - phase-I2-product-and-scope-delta",
                    "  - phase-I3-architecture-and-contract-delta",
                    "  - phase-I4-frontend-design-delta",
                    "  - phase-I5-frontend-implementation-delta",
                    "  - phase-I6-integration-and-regression-review",
                    "  - phase-I7-change-acceptance",
                ]
            )
            + "\n",
        )
        self.write(repo_root, "runs/current/changes/CR-1/impact-manifest.yaml", "change_id: CR-1\n")
        self.write(repo_root, "runs/current/changes/CR-1/reopened-gates.md", "# Reopened Gates\n- Frontend revalidation\n")
        self.write(
            repo_root,
            "runs/current/changes/CR-1/affected-artifacts.md",
            "\n".join(
                [
                    "# Affected Artifacts",
                    "",
                    "- `runs/current/artifacts/ux/navigation.md`",
                    "- `runs/current/artifacts/backend-design/model-design.md`",
                    "- `runs/current/changes/CR-1/candidate/artifacts/ux/screen-delta.md`",
                ]
            )
            + "\n",
        )
        self.write(
            repo_root,
            "runs/current/changes/CR-1/affected-candidate-artifacts.md",
            "\n".join(
                [
                    "# Affected Candidate Artifacts",
                    "",
                    "- `runs/current/changes/CR-1/candidate/artifacts/ux/screen-delta.md`",
                ]
            )
            + "\n",
        )
        self.write(
            repo_root,
            "runs/current/changes/CR-1/affected-app-paths.md",
            "\n".join(
                [
                    "# Affected App Paths",
                    "",
                    "- `app/frontend/src/App.tsx`",
                    "- `app/backend/src/service.py`",
                ]
            )
            + "\n",
        )
        self.write(
            repo_root,
            "runs/current/changes/CR-1/role-loads/frontend.yaml",
            "\n".join(
                [
                    "change_id: CR-1",
                    "read_artifacts:",
                    "  - runs/current/artifacts/ux/navigation.md",
                    "candidate_artifacts:",
                    "  - runs/current/changes/CR-1/candidate/artifacts/ux/screen-delta.md",
                    "read_app_paths:",
                    "  - app/frontend/src/App.tsx",
                    "write_app_paths:",
                    "  - app/frontend/src/App.tsx",
                    "verification_inputs:",
                    "  - runs/current/changes/CR-1/verification/regression-plan.md",
                ]
            )
            + "\n",
        )
        self.write(
            repo_root,
            "runs/current/changes/CR-1/role-loads/backend.yaml",
            "\n".join(
                [
                    "change_id: CR-1",
                    "scope_profile: frontend-only",
                    "read_artifacts:",
                    "  - runs/current/changes/CR-1/request.md",
                    "candidate_artifacts: []",
                    "write_artifacts: []",
                    "read_app_paths: []",
                    "write_app_paths: []",
                    "required_feature_packs: []",
                    "verification_inputs:",
                    "  - runs/current/changes/CR-1/verification/backend-check.md",
                ]
            )
            + "\n",
        )
        return repo_root

    def test_change_run_reads_role_load_manifest_and_exact_scoped_paths(self) -> None:
        repo_root = self.build_repo()

        packet = resolve_read_packet(
            repo_root,
            "frontend",
            explicit_task_bundle="playbook/task-bundles/frontend-implementation.yaml",
        )
        read_paths = packet["read_paths"]

        self.assertIn("runs/current/changes/CR-1/request.md", read_paths)
        self.assertIn("runs/current/changes/CR-1/affected-artifacts.md", read_paths)
        self.assertIn("runs/current/changes/CR-1/affected-candidate-artifacts.md", read_paths)
        self.assertIn("runs/current/changes/CR-1/affected-app-paths.md", read_paths)
        self.assertIn("runs/current/changes/CR-1/role-loads/frontend.yaml", read_paths)
        self.assertIn("runs/current/artifacts/ux/navigation.md", read_paths)
        self.assertIn("runs/current/changes/CR-1/candidate/artifacts/ux/screen-delta.md", read_paths)
        self.assertIn("runs/current/changes/CR-1/verification/regression-plan.md", read_paths)
        self.assertIn("app/frontend/src/App.tsx", read_paths)
        self.assertNotIn("runs/current/artifacts/backend-design/model-design.md", read_paths)
        self.assertNotIn("app/backend/src/service.py", read_paths)

    def test_change_run_reads_binding_external_references_and_requested_skills(self) -> None:
        repo_root = self.build_repo()
        self.write(
            repo_root,
            "skills/mui-db-admin-ux/SKILL.md",
            "# skill\n",
        )
        self.write(
            repo_root,
            "runs/current/changes/CR-1/external-references/README.md",
            "# External References\n",
        )
        self.write(
            repo_root,
            "runs/current/changes/CR-1/external-references/sonic/src/App.tsx",
            "export default function App() { return null; }\n",
        )
        manifest = {
            "priority_order": [
                "input-prompt",
                "business-model-and-contracts",
                "external-references",
                "agent-interpretation",
            ],
            "requested_skill_paths": ["skills/mui-db-admin-ux/SKILL.md"],
            "references": [
                {
                    "label": "sonic",
                    "source_path": "/tmp/sonic.zip",
                    "category": "visual-ui",
                    "fidelity": "mimic-look-and-feel",
                    "roles": ["frontend", "qa"],
                    "materialized_path": "external-references/sonic",
                    "key_files": [
                        "external-references/sonic/src/App.tsx",
                    ],
                }
            ],
        }
        self.write(
            repo_root,
            "runs/current/changes/CR-1/external-references/manifest.json",
            json.dumps(manifest, indent=2) + "\n",
        )

        packet = resolve_read_packet(
            repo_root,
            "frontend",
            explicit_task_bundle="playbook/task-bundles/frontend-implementation.yaml",
        )
        read_paths = packet["read_paths"]

        self.assertIn("runs/current/changes/CR-1/external-references/manifest.json", read_paths)
        self.assertIn("runs/current/changes/CR-1/external-references/README.md", read_paths)
        self.assertIn("skills/mui-db-admin-ux/SKILL.md", read_paths)
        self.assertIn("runs/current/changes/CR-1/external-references/sonic", read_paths)
        self.assertIn("runs/current/changes/CR-1/external-references/sonic/src/App.tsx", read_paths)

    def test_change_run_falls_back_to_affected_scope_when_role_load_is_placeholder(self) -> None:
        repo_root = self.build_repo()
        self.write(
            repo_root,
            "runs/current/changes/CR-1/role-loads/frontend.yaml",
            "\n".join(
                [
                    "change_id: CR-1",
                    "read_artifacts:",
                    "  - Fill with exact baseline or candidate artifacts for this role.",
                    "candidate_artifacts:",
                    "  - Fill with exact candidate artifacts this role may edit.",
                    "read_app_paths:",
                    "  - Fill with exact app paths this role may read.",
                    "write_app_paths:",
                    "  - Fill with exact app paths this role may change.",
                    "verification_inputs:",
                    "  - Fill with exact regression or evidence files required for this role.",
                ]
            )
            + "\n",
        )

        packet = resolve_read_packet(
            repo_root,
            "frontend",
            explicit_task_bundle="playbook/task-bundles/frontend-implementation.yaml",
        )
        read_paths = packet["read_paths"]

        self.assertIn("runs/current/artifacts/ux/navigation.md", read_paths)
        self.assertIn("runs/current/changes/CR-1/candidate/artifacts/ux/screen-delta.md", read_paths)
        self.assertIn("app/frontend/src/App.tsx", read_paths)
        self.assertNotIn("runs/current/artifacts/backend-design/model-design.md", read_paths)
        self.assertNotIn("app/backend/src/service.py", read_paths)

    def test_packet_health_requires_populated_role_load_for_late_change_phase(self) -> None:
        repo_root = self.build_repo()
        self.write(
            repo_root,
            "runs/current/changes/CR-1/role-loads/frontend.yaml",
            "\n".join(
                [
                    "change_id: CR-1",
                    "read_artifacts:",
                    "  - Fill with exact baseline or candidate artifacts for this role.",
                    "candidate_artifacts:",
                    "  - Fill with exact candidate artifacts this role may edit.",
                    "read_app_paths:",
                    "  - Fill with exact app paths this role may read.",
                ]
            )
            + "\n",
        )

        packet = resolve_read_packet(
            repo_root,
            "frontend",
            explicit_task_bundle="playbook/task-bundles/frontend-implementation.yaml",
        )
        issues = collect_packet_health_issues(
            repo_root,
            "frontend",
            packet,
            explicit_phase="phase-I5-frontend-implementation-delta",
        )

        self.assertTrue(any("template placeholder" in issue for issue in issues))

    def test_packet_health_ignores_early_change_phase_placeholder_role_load(self) -> None:
        repo_root = self.build_repo()
        self.write(
            repo_root,
            "runs/current/changes/CR-1/role-loads/frontend.yaml",
            "\n".join(
                [
                    "change_id: CR-1",
                    "read_artifacts:",
                    "  - Fill with exact baseline or candidate artifacts for this role.",
                ]
            )
            + "\n",
        )

        packet = resolve_read_packet(
            repo_root,
            "frontend",
            explicit_task_bundle="playbook/task-bundles/frontend-implementation.yaml",
        )
        issues = collect_packet_health_issues(
            repo_root,
            "frontend",
            packet,
            explicit_phase="phase-I3-architecture-and-contract-delta",
        )

        self.assertEqual(issues, [])

    def test_parse_yaml_subset_accepts_same_indent_list_style(self) -> None:
        repo_root = self.build_repo()
        manifest = repo_root / "runs/current/changes/CR-1/role-loads/backend.yaml"
        self.write(
            repo_root,
            "runs/current/changes/CR-1/role-loads/backend.yaml",
            "\n".join(
                [
                    "change_id: CR-1",
                    "read_artifacts:",
                    "- runs/current/changes/CR-1/request.md",
                    "- runs/current/changes/CR-1/classification.yaml",
                    "read_app_paths:",
                    "- app/backend/src",
                    "write_app_paths:",
                    "- app/backend/src",
                ]
            )
            + "\n",
        )

        payload = parse_yaml_subset(manifest)

        self.assertEqual(
            payload["read_artifacts"],
            [
                "runs/current/changes/CR-1/request.md",
                "runs/current/changes/CR-1/classification.yaml",
            ],
        )
        self.assertEqual(payload["read_app_paths"], ["app/backend/src"])
        self.assertEqual(payload["write_app_paths"], ["app/backend/src"])

    def test_parse_yaml_subset_accepts_indented_empty_list_style(self) -> None:
        repo_root = self.build_repo()
        manifest = repo_root / "runs/current/changes/CR-1/role-loads/frontend.yaml"
        self.write(
            repo_root,
            "runs/current/changes/CR-1/role-loads/frontend.yaml",
            "\n".join(
                [
                    "change_id: CR-1",
                    "write_artifacts:",
                    "  []",
                    "required_feature_packs:",
                    "  []",
                    "write_app_paths:",
                    "  - app/frontend/**",
                ]
            )
            + "\n",
        )

        payload = parse_yaml_subset(manifest)

        self.assertEqual(payload["write_artifacts"], [])
        self.assertEqual(payload["required_feature_packs"], [])
        self.assertEqual(payload["write_app_paths"], ["app/frontend/**"])

    def test_parse_yaml_subset_accepts_inline_empty_list_style(self) -> None:
        repo_root = self.build_repo()
        manifest = repo_root / "runs/current/changes/CR-1/role-loads/backend.yaml"

        payload = parse_yaml_subset(manifest)

        self.assertEqual(payload["candidate_artifacts"], [])
        self.assertEqual(payload["write_artifacts"], [])
        self.assertEqual(payload["read_app_paths"], [])
        self.assertEqual(payload["write_app_paths"], [])
        self.assertEqual(payload["required_feature_packs"], [])

    def test_parse_yaml_subset_accepts_folded_block_scalar(self) -> None:
        repo_root = self.build_repo()
        manifest = repo_root / "runs/current/changes/CR-1/role-loads/product_manager.yaml"
        self.write(
            repo_root,
            "runs/current/changes/CR-1/role-loads/product_manager.yaml",
            "\n".join(
                [
                    "change_id: CR-1",
                    "baseline_id: >",
                    "  Accepted playlist app baseline with product publication drift handled via",
                    "  runs/current/changes/CR-0/candidate/artifacts/product/** and",
                    "  runs/current/changes/CR-00/candidate/artifacts/product/**.",
                    "read_artifacts:",
                    "  - runs/current/changes/CR-1/request.md",
                ]
            )
            + "\n",
        )

        payload = parse_yaml_subset(manifest)

        self.assertEqual(
            payload["baseline_id"],
            "Accepted playlist app baseline with product publication drift handled via "
            "runs/current/changes/CR-0/candidate/artifacts/product/** and "
            "runs/current/changes/CR-00/candidate/artifacts/product/**.",
        )
        self.assertEqual(payload["read_artifacts"], ["runs/current/changes/CR-1/request.md"])

    def test_parse_yaml_subset_accepts_multiline_quoted_scalar_and_wrapped_list_item(self) -> None:
        repo_root = self.build_repo()
        manifest = repo_root / "runs/current/changes/CR-1/role-loads/frontend.yaml"
        self.write(
            repo_root,
            "runs/current/changes/CR-1/role-loads/frontend.yaml",
            "\n".join(
                [
                    "change_id: CR-1",
                    "baseline_id: 'accepted baseline still sourced from",
                    "  runs/current/changes/CR-0/candidate/artifacts/product/**",
                    "  and runs/current/changes/CR-00/candidate/artifacts/product/**.'",
                    "required_feature_packs:",
                    "  - dnd-kit (accepted baseline scope only for playlist lineup drag-and-drop; not reopened",
                    "    by this change)",
                ]
            )
            + "\n",
        )

        payload = parse_yaml_subset(manifest)

        self.assertEqual(
            payload["baseline_id"],
            "accepted baseline still sourced from "
            "runs/current/changes/CR-0/candidate/artifacts/product/** "
            "and runs/current/changes/CR-00/candidate/artifacts/product/**.",
        )
        self.assertEqual(
            payload["required_feature_packs"],
            ["dnd-kit (accepted baseline scope only for playlist lineup drag-and-drop; not reopened by this change)"],
        )

    def test_change_run_writable_scope_is_narrowed_by_populated_role_load_manifest(self) -> None:
        repo_root = self.build_repo()

        writable = resolve_writable_paths(
            repo_root,
            "frontend",
            explicit_task_bundle="playbook/task-bundles/frontend-implementation.yaml",
        )

        self.assertIn("runs/current/role-state/*/inbox/*.md", writable)
        self.assertIn("runs/current/role-state/frontend/context.md", writable)
        self.assertIn("app/frontend/src/App.tsx", writable)
        self.assertIn("runs/current/changes/CR-1/candidate/artifacts/ux/screen-delta.md", writable)
        self.assertIn("runs/current/changes/CR-1/verification/regression-plan.md", writable)
        self.assertNotIn("app/frontend/**", writable)
        self.assertNotIn("runs/current/artifacts/ux/**", writable)
        self.assertNotIn("runs/current/changes/*/candidate/artifacts/ux/**", writable)

    def test_change_run_writable_scope_honors_write_artifacts_in_role_load_manifest(self) -> None:
        repo_root = self.build_repo()
        self.write(
            repo_root,
            "runs/current/changes/CR-1/role-loads/frontend.yaml",
            "\n".join(
                [
                    "change_id: CR-1",
                    "read_artifacts:",
                    "  - runs/current/artifacts/ux/navigation.md",
                    "candidate_artifacts:",
                    "  - runs/current/changes/CR-1/candidate/artifacts/ux/screen-delta.md",
                    "write_artifacts:",
                    "  - runs/current/artifacts/ux/navigation.md",
                    "read_app_paths:",
                    "  - app/frontend/src/App.tsx",
                    "write_app_paths:",
                    "  - app/frontend/src/App.tsx",
                    "verification_inputs:",
                    "  - runs/current/changes/CR-1/verification/regression-plan.md",
                ]
            )
            + "\n",
        )

        writable = resolve_writable_paths(
            repo_root,
            "frontend",
            explicit_task_bundle="playbook/task-bundles/frontend-implementation.yaml",
        )

        self.assertIn("runs/current/artifacts/ux/navigation.md", writable)
        self.assertIn("runs/current/changes/CR-1/candidate/artifacts/ux/screen-delta.md", writable)
        self.assertIn("app/frontend/src/App.tsx", writable)
        self.assertIn("runs/current/changes/CR-1/verification/regression-plan.md", writable)
        self.assertNotIn("runs/current/artifacts/ux/**", writable)
        self.assertNotIn("runs/current/changes/*/candidate/artifacts/ux/**", writable)

    def test_architect_narrowing_preserves_canonical_architecture_scope_when_role_load_only_targets_change_packet_files(self) -> None:
        repo_root = self.build_repo()
        self.write(
            repo_root,
            "playbook/routing/role-core.yaml",
            "\n".join(
                [
                    "architect:",
                    "  always_load:",
                    "    - playbook/summaries/global-core.md",
                    "  writable:",
                    "    - runs/current/artifacts/architecture/**",
                    "    - runs/current/evidence/contract-samples.md",
                    "    - runs/current/role-state/architect/**",
                    "    - runs/current/changes/*/candidate/artifacts/architecture/**",
                    "    - runs/current/changes/*/role-loads/**",
                    "  cannot_write:",
                    "    - app/**",
                ]
            )
            + "\n",
        )
        self.write(
            repo_root,
            "playbook/task-bundles/integration-review.yaml",
            "\n".join(
                [
                    "name: integration-review",
                    "role: architect",
                    "required_phase:",
                    "  - playbook/process/phases/phase-I6-integration-and-regression-review.md",
                    "writable_targets:",
                    "  - runs/current/artifacts/architecture/**",
                    "  - runs/current/evidence/contract-samples.md",
                ]
            )
            + "\n",
        )
        self.write(
            repo_root,
            "runs/current/changes/CR-1/role-loads/architect.yaml",
            "\n".join(
                [
                    "change_id: CR-1",
                    "read_artifacts:",
                    "  - runs/current/changes/CR-1/role-loads/architect.yaml",
                    "candidate_artifacts:",
                    "  - runs/current/changes/CR-1/candidate/artifacts/architecture/observer-product-scope-delta.md",
                    "write_artifacts:",
                    "  - runs/current/changes/CR-1/role-loads/architect.yaml",
                    "  - runs/current/changes/CR-1/candidate/artifacts/architecture/observer-product-scope-delta.md",
                    "read_app_paths: []",
                    "write_app_paths: []",
                    "verification_inputs:",
                    "  - /tmp/sentient/src/components/Layout.tsx",
                ]
            )
            + "\n",
        )

        writable = resolve_writable_paths(
            repo_root,
            "architect",
            explicit_task_bundle="playbook/task-bundles/integration-review.yaml",
        )

        self.assertIn("runs/current/artifacts/architecture/**", writable)
        self.assertIn("runs/current/evidence/contract-samples.md", writable)
        self.assertIn("runs/current/changes/CR-1/candidate/artifacts/architecture/observer-product-scope-delta.md", writable)
        self.assertIn("runs/current/changes/CR-1/role-loads/architect.yaml", writable)

    def test_backend_inline_empty_role_load_lists_do_not_drop_backend_write_scope(self) -> None:
        repo_root = self.build_repo()

        writable = resolve_writable_paths(
            repo_root,
            "backend",
            explicit_task_bundle="playbook/task-bundles/change-backend-implementation.yaml",
        )

        self.assertNotIn("[]", writable)
        self.assertIn("app/backend/**", writable)
        self.assertIn("app/rules/**", writable)
        self.assertIn("runs/current/changes/CR-1/verification/backend-check.md", writable)

    def test_forbidden_paths_and_diff_validation_enforce_cannot_write(self) -> None:
        repo_root = self.build_repo()

        self.assertIn("app/backend/**", resolve_forbidden_paths(repo_root, "architect"))
        self.assertTrue(is_allowed_change(repo_root, "architect", "app/frontend/src/App.tsx", []))
        self.assertFalse(is_allowed_change(repo_root, "architect", "app/backend/src/service.py", []))


if __name__ == "__main__":
    unittest.main()
