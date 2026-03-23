from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from routing_resolver import resolve_forbidden_paths, resolve_read_packet, resolve_writable_paths
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
                    "writable_targets:",
                    "  - app/frontend/**",
                    "  - runs/current/artifacts/ux/**",
                    "  - runs/current/changes/*/candidate/artifacts/ux/**",
                    "  - runs/current/changes/*/verification/**",
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
        self.write(repo_root, "runs/current/changes/CR-1/classification.yaml", "kind: change\n")
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
        self.assertIn("runs/current/changes/CR-1/affected-app-paths.md", read_paths)
        self.assertIn("runs/current/changes/CR-1/role-loads/frontend.yaml", read_paths)
        self.assertIn("runs/current/artifacts/ux/navigation.md", read_paths)
        self.assertIn("runs/current/changes/CR-1/candidate/artifacts/ux/screen-delta.md", read_paths)
        self.assertIn("runs/current/changes/CR-1/verification/regression-plan.md", read_paths)
        self.assertIn("app/frontend/src/App.tsx", read_paths)
        self.assertNotIn("runs/current/artifacts/backend-design/model-design.md", read_paths)
        self.assertNotIn("app/backend/src/service.py", read_paths)

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

    def test_forbidden_paths_and_diff_validation_enforce_cannot_write(self) -> None:
        repo_root = self.build_repo()

        self.assertIn("app/backend/**", resolve_forbidden_paths(repo_root, "architect"))
        self.assertTrue(is_allowed_change(repo_root, "architect", "app/frontend/src/App.tsx", []))
        self.assertFalse(is_allowed_change(repo_root, "architect", "app/backend/src/service.py", []))


if __name__ == "__main__":
    unittest.main()
