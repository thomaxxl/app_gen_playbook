from __future__ import annotations

import tempfile
import unittest
import unittest.mock
from pathlib import Path

import yaml

from recover_run_queue import (
    ArtifactNeed,
    RuntimeEnvironmentEscalation,
    collect_completion_blocker_needs,
    select_recovery_targets,
    write_stalled_run_triage_notes,
    write_phase_ceo_review_notes,
    write_recovery_notes,
    write_runtime_environment_notes,
    write_source_scope_notes,
)


def write_template(path: Path, owner: str, phase: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"owner: {owner}",
                f"phase: {phase}",
                "status: stub",
                "depends_on:",
                "  - runs/current/input.md",
                "unresolved:",
                "  - replace with run-specific decision",
                f"last_updated_by: {owner}",
                "---",
                "",
                f"# {path.stem}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_run_artifact(path: Path, status: str = "ready-for-handoff") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "owner: test",
                "phase: test-phase",
                f"status: {status}",
                "depends_on:",
                "  - runs/current/input.md",
                "unresolved:",
                "  - none",
                "last_updated_by: test",
                "---",
                "",
                "# generated",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_role_dirs(repo_root: Path, role: str) -> None:
    for subdir in ("inbox", "inflight", "processed"):
        (repo_root / "runs" / "current" / "role-state" / role / subdir).mkdir(parents=True, exist_ok=True)


def write_app_baseline(repo_root: Path) -> None:
    for relative in (
        "app/README.md",
        "app/.gitignore",
        "app/install.sh",
        "app/run.sh",
        "app/Dockerfile",
        "app/docker-compose.yml",
        "app/frontend/package.json",
        "app/frontend/vite.config.ts",
        "app/backend/requirements.txt",
        "app/backend/run.py",
        "app/rules/rules.py",
        "app/reference/admin.yaml",
        "app/frontend/src/App.tsx",
        "app/frontend/src/Home.tsx",
    ):
        write_file(repo_root / relative, "generated\n")


def write_recovery_validation_baseline(repo_root: Path) -> None:
    write_file(repo_root / "runs/current/remarks.md", "# Run Remarks\n")
    write_file(repo_root / "runs/current/notes.md", "# Run Notes\n")
    write_file(
        repo_root / "runs/current/orchestrator/run-status.json",
        '{\n  "mode": "iterative-change-run",\n  "current_phase": "phase-6-integration-review"\n}\n',
    )
    write_file(repo_root / "runs/current/evidence/orchestrator/logs/orchestrator.log", "orchestrator log\n")
    write_file(repo_root / "playbook/process/quality-gates.md", "# Quality Gates\n")
    write_file(repo_root / "tools/compile_final_review_pack.py", "print('stub')\n")
    write_file(
        repo_root / "runs/current/evidence/ui-previews/manifest.md",
        "# UI Preview Manifest\n\ncapture_status: not-required\n",
    )
    write_run_artifact(repo_root / "runs/current/artifacts/architecture/integration-review.md")

    for relative in (
        "playbook/task-bundles/phase-1-product-definition.yaml",
        "playbook/task-bundles/phase-2-architecture-contract.yaml",
        "playbook/task-bundles/ux-design.yaml",
        "playbook/task-bundles/backend-design.yaml",
        "playbook/task-bundles/backend-implementation.yaml",
        "playbook/task-bundles/integration-review.yaml",
        "playbook/task-bundles/acceptance-review.yaml",
    ):
        write_file(
            repo_root / relative,
            "name: stub\n",
        )

    for relative in (
        "playbook/process/phases/phase-1-product-definition.md",
        "playbook/process/phases/phase-2-architecture-contract.md",
        "playbook/process/phases/phase-3-ux-and-interaction-design.md",
        "playbook/process/phases/phase-4-backend-design-and-rules-mapping.md",
        "playbook/process/phases/phase-5-parallel-implementation.md",
        "playbook/process/phases/phase-6-integration-review.md",
        "playbook/process/phases/phase-7-product-acceptance.md",
        "specs/product/README.md",
        "specs/architecture/README.md",
        "specs/ux/README.md",
        "specs/backend-design/README.md",
        "specs/architecture/integration-review.md",
        "specs/product/acceptance-review.md",
    ):
        write_file(repo_root / relative, "# support\n")


def write_required_phase6_evidence(repo_root: Path) -> None:
    write_file(
        repo_root / "runs/current/evidence/contract-samples.md",
        "\n".join(
            [
                "# Contract Samples",
                "",
                "## SAFRS resource coverage",
                "- discovered from /jsonapi.json",
                "",
                "## Relationship coverage",
                "- relationship proof present",
                "",
                "## Approved non-SAFRS exceptions",
                "- none",
                "",
            ]
        ),
    )
    write_file(repo_root / "runs/current/evidence/frontend-usability.md", "reviewed\n")
    write_file(repo_root / "runs/current/evidence/frontend-browser-proof.md", "reviewed\n")
    write_file(
        repo_root / "runs/current/evidence/ui-previews/manifest.md",
        "\n".join(
            [
                "# UI Preview Manifest",
                "",
                "capture_status: not-required",
                "",
            ]
        ),
    )
    for relative in (
        "runs/current/evidence/quality/crud-matrix.md",
        "runs/current/evidence/quality/data-sourcing-audit.md",
        "runs/current/evidence/quality/seed-data-audit.md",
        "runs/current/evidence/quality/ui-copy-audit.md",
        "runs/current/evidence/quality/test-results.md",
        "runs/current/evidence/quality/quality-summary.md",
        "runs/current/evidence/quality/coverage-report.md",
    ):
        write_file(repo_root / relative, "# evidence\n")
    write_file(
        repo_root / "runs/current/evidence/quality/review-plan.json",
        '{\n  "starter_status": "pending-review-evidence",\n  "surfaces": []\n}\n',
    )


class RecoverRunQueueTests(unittest.TestCase):
    def test_collect_completion_blocker_needs_includes_story_review_frontend_route_and_search_review_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()

            blockers = [
                {
                    "kind": "frontend-route-coverage",
                    "owner": "frontend",
                    "phase": "phase-5-parallel-implementation",
                    "path": "app/frontend/src/App.tsx",
                    "reason": "missing required story-supporting route ROUTE-PLAYLIST-LIST at /app/#/Playlist",
                },
                {
                    "kind": "preview-coverage",
                    "owner": "architect",
                    "phase": "phase-6-integration-review",
                    "path": "runs/current/evidence/ui-previews/manifest.md",
                    "reason": "preview manifest is missing structured preview coverage for required story US-007",
                },
                {
                    "kind": "ui-preview-scroll-validation-missing",
                    "owner": "architect",
                    "phase": "phase-6-integration-review",
                    "path": "runs/current/evidence/ui-previews/manifest.md",
                    "reason": "captured ui preview manifest must declare scroll_state_validation: reviewed",
                },
                {
                    "kind": "ui-preview-shell-continuity-missing",
                    "owner": "architect",
                    "phase": "phase-6-integration-review",
                    "path": "runs/current/evidence/ui-previews/manifest.md",
                    "reason": "captured ui preview manifest must declare shell_continuity_validation: approved",
                },
                {
                    "kind": "integration-review-coverage",
                    "owner": "architect",
                    "phase": "phase-6-integration-review",
                    "path": "runs/current/artifacts/architecture/integration-review.md",
                    "reason": "integration review is missing Story Coverage row for US-007",
                },
                {
                    "kind": "search-review-fallback-accepted",
                    "owner": "architect",
                    "phase": "phase-6-integration-review",
                    "path": "runs/current/evidence/frontend-browser-proof.md",
                    "reason": "frontend browser proof still accepts a search fallback posture (approved-with-frontend-fallbacks) instead of approved search relevance",
                },
                {
                    "kind": "search-browser-proof-incomplete",
                    "owner": "architect",
                    "phase": "phase-6-integration-review",
                    "path": "runs/current/evidence/frontend-browser-proof.md",
                    "reason": "frontend browser proof must declare search_query_alignment_validation: approved for shipped custom search, found missing",
                },
                {
                    "kind": "search-usability-review-incomplete",
                    "owner": "architect",
                    "phase": "phase-6-integration-review",
                    "path": "runs/current/evidence/frontend-usability.md",
                    "reason": "frontend usability review must declare search_relevance_validation: approved for shipped custom search, found missing",
                },
                {
                    "kind": "acceptance-review-coverage",
                    "owner": "product_manager",
                    "phase": "phase-7-product-acceptance",
                    "path": "runs/current/artifacts/product/acceptance-review.md",
                    "reason": "acceptance review is missing Story Coverage row for US-007",
                },
                {
                    "kind": "final-review-pack-incomplete",
                    "owner": "product_manager",
                    "phase": "phase-7-product-acceptance",
                    "path": "runs/current/evidence/final/review-index.md",
                    "reason": "final review pack index is missing",
                },
                {
                    "kind": "qa-review-coverage",
                    "owner": "qa",
                    "phase": "phase-8-qa-pre-delivery-validation",
                    "path": "runs/current/evidence/qa-delivery-review.md",
                    "reason": "QA review story US-007 is missing screenshot proof",
                },
            ]

            with unittest.mock.patch("recover_run_queue.collect_blockers", return_value=blockers):
                needs = collect_completion_blocker_needs(repo_root)

            self.assertEqual(
                [(need.role, need.phase, need.path.relative_to(repo_root).as_posix()) for need in needs],
                [
                    ("frontend", "phase-5-parallel-implementation", "app/frontend/src/App.tsx"),
                    ("architect", "phase-6-integration-review", "runs/current/evidence/ui-previews/manifest.md"),
                    ("architect", "phase-6-integration-review", "runs/current/evidence/ui-previews/manifest.md"),
                    ("architect", "phase-6-integration-review", "runs/current/evidence/ui-previews/manifest.md"),
                    ("architect", "phase-6-integration-review", "runs/current/artifacts/architecture/integration-review.md"),
                    ("architect", "phase-6-integration-review", "runs/current/evidence/frontend-browser-proof.md"),
                    ("architect", "phase-6-integration-review", "runs/current/evidence/frontend-browser-proof.md"),
                    ("architect", "phase-6-integration-review", "runs/current/evidence/frontend-usability.md"),
                    ("product_manager", "phase-7-product-acceptance", "runs/current/artifacts/product/acceptance-review.md"),
                    ("product_manager", "phase-7-product-acceptance", "runs/current/evidence/final/review-index.md"),
                    ("qa", "phase-8-qa-pre-delivery-validation", "runs/current/evidence/qa-delivery-review.md"),
                ],
            )

    def test_orchestrator_source_scope_escalation_creates_ceo_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_recovery_validation_baseline(repo_root)
            for role in ("orchestrator", "ceo"):
                ensure_role_dirs(repo_root, role)
            write_file(repo_root / "specs/contracts/frontend/validation.md", "# frontend validation\n")
            write_file(repo_root / "playbook/process/phases/phase-6-integration-review.md", "# phase 6\n")

            escalation = repo_root / "runs/current/role-state/orchestrator/inbox/20260329-212400-from-architect-to-orchestrator-preview-status-gate-vs-enum-write-scope.md"
            write_file(
                escalation,
                "\n".join(
                    [
                        "from: architect",
                        "to: orchestrator",
                        "topic: preview-status-gate-vs-enum-write-scope",
                        "purpose: route a source-contract contradiction to a write-scope-capable turn",
                        "",
                        "## Required Reads",
                        "- runs/current/evidence/ui-previews/manifest.md",
                        "- specs/contracts/frontend/validation.md",
                        "- playbook/process/phases/phase-6-integration-review.md",
                        "",
                        "## Requested Outputs",
                        "- schedule a turn that can edit `specs/contracts/frontend/validation.md`",
                        "- schedule a turn that can edit `playbook/process/phases/phase-6-integration-review.md`",
                        "",
                        "## Gate Status",
                        "- blocked",
                        "",
                        "## Blocking Issues",
                        "- architect runtime cannot edit the required source files",
                        "",
                    ]
                ),
            )

            created = write_source_scope_notes(repo_root, "")
            self.assertEqual(len(created), 1)

            ceo_note = created[0]
            self.assertIn("/role-state/ceo/inbox/", ceo_note.as_posix())
            note_text = ceo_note.read_text(encoding="utf-8")
            self.assertIn("to: ceo", note_text)
            self.assertIn("edit `specs/contracts/frontend/validation.md`", note_text)
            self.assertIn("edit `playbook/process/phases/phase-6-integration-review.md`", note_text)

            archived = repo_root / "runs/current/role-state/orchestrator/processed/20260329-212400-from-architect-to-orchestrator-preview-status-gate-vs-enum-write-scope.escalated.md"
            self.assertTrue(archived.exists())
            self.assertFalse(escalation.exists())
            self.assertIn(archived.relative_to(repo_root).as_posix(), note_text)
            self.assertNotIn(escalation.relative_to(repo_root).as_posix(), note_text)

    def test_source_scope_escalation_can_infer_requested_path_from_required_reads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_recovery_validation_baseline(repo_root)
            for role in ("orchestrator", "ceo"):
                ensure_role_dirs(repo_root, role)
            write_file(repo_root / "playbook/process/phases/phase-6-integration-review.md", "# phase 6\n")
            write_file(repo_root / "specs/architecture/integration-review.md", "# integration review\n")
            write_run_artifact(repo_root / "runs/current/artifacts/architecture/integration-review.md")

            escalation = repo_root / "runs/current/role-state/orchestrator/inbox/20260330-074500-from-architect-to-orchestrator-preview-status-source-repair.md"
            write_file(
                escalation,
                "\n".join(
                    [
                        "from: architect",
                        "to: orchestrator",
                        "topic: preview-status-source-repair",
                        "purpose: route the required source-maintenance follow-up",
                        "",
                        "## Required Reads",
                        "- runs/current/artifacts/architecture/integration-review.md",
                        "- playbook/process/phases/phase-6-integration-review.md",
                        "- specs/architecture/integration-review.md",
                        "",
                        "## Requested Outputs",
                        "- route a source-maintenance turn that updates the normative preview-status contract",
                        "",
                        "## Gate Status",
                        "- blocked",
                        "",
                        "## Notes",
                        "- no change is required in `specs/architecture/integration-review.md`; the repair belongs in the Phase 6 process source",
                        "",
                    ]
                ),
            )

            created = write_source_scope_notes(repo_root, "")
            self.assertEqual(len(created), 1)
            note_text = created[0].read_text(encoding="utf-8")
            self.assertIn("edit `playbook/process/phases/phase-6-integration-review.md`", note_text)
            self.assertNotIn("edit `specs/architecture/integration-review.md`", note_text)
            self.assertNotIn("edit `playbook/spec`", note_text)

    def test_runtime_environment_escalation_creates_ceo_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_recovery_validation_baseline(repo_root)
            for role in ("orchestrator", "ceo"):
                ensure_role_dirs(repo_root, role)

            escalation = repo_root / "runs/current/role-state/orchestrator/inbox/20260330-142032-from-architect-to-orchestrator-phase6-recovery-still-blocked.md"
            write_file(
                escalation,
                "\n".join(
                    [
                        "from: architect",
                        "to: orchestrator",
                        "topic: phase6-recovery-still-blocked",
                        "purpose: report that the canonical architect integration-review artifact was refreshed from the current evidence pack, but Phase 6 remains blocked on browser-runtime proof",
                        "",
                        "## Remaining Blockers",
                        "- `runs/current/evidence/ui-previews/manifest.md` remains `capture_status: runtime-failed`",
                        "- browser-reviewed story-first proof is still missing",
                        "- the browser lane is unstable and later same-day reruns fail during Chromium launch before first render",
                        "",
                        "## Next Routing Need",
                        "- route the next action as a runtime/environment recovery decision rather than another architect contract repair",
                        "",
                    ]
                ),
            )

            created = write_runtime_environment_notes(repo_root, "")
            self.assertEqual(len(created), 1)

            ceo_note = created[0]
            self.assertIn("/role-state/ceo/inbox/", ceo_note.as_posix())
            note_text = ceo_note.read_text(encoding="utf-8")
            self.assertIn("to: ceo", note_text)
            self.assertIn("runtime or environment blocker", note_text)
            self.assertIn("runs/current/orchestrator/operator-action-required.md", note_text)

            archived = repo_root / "runs/current/role-state/orchestrator/processed/20260330-142032-from-architect-to-orchestrator-phase6-recovery-still-blocked.escalated.md"
            self.assertTrue(archived.exists())
            self.assertFalse(escalation.exists())
            self.assertIn(archived.relative_to(repo_root).as_posix(), note_text)

    def test_runtime_environment_escalation_can_include_source_scope_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_recovery_validation_baseline(repo_root)
            for role in ("orchestrator", "ceo"):
                ensure_role_dirs(repo_root, role)

            escalation = repo_root / "runs/current/role-state/orchestrator/inbox/20260330-151949-from-architect-to-orchestrator-phase-6-browser-blocker.md"
            write_file(
                escalation,
                "\n".join(
                    [
                        "from: architect",
                        "to: orchestrator",
                        "topic: phase-6-browser-blocker",
                        "purpose: keep the recovery queue explicit because integration review is still blocked by a non-architect runtime blocker",
                        "",
                        "## Blocking Issues",
                        "- preview capture still crashes before first screenshot during Chromium launch",
                        "- preview-status source-scope wording is still unresolved",
                        "",
                        "## Next Routing Need",
                        "- route the next action as a runtime/environment recovery decision rather than another architect contract repair",
                        "",
                    ]
                ),
            )

            created = write_runtime_environment_notes(repo_root, "")
            self.assertEqual(len(created), 1)
            note_text = created[0].read_text(encoding="utf-8")
            self.assertIn("to: ceo", note_text)
            self.assertIn("runtime or environment blocker", note_text)

    def test_phase_ceo_review_note_is_created_when_phase_outputs_are_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_recovery_validation_baseline(repo_root)
            ensure_role_dirs(repo_root, "ceo")
            write_file(
                repo_root / "runs/current/orchestrator/run-status.json",
                '{\n  "mode": "new-full-run",\n  "current_phase": "phase-3-ux-and-interaction-design"\n}\n',
            )
            write_file(
                repo_root / "playbook/process/phases/phase-3-ux-and-interaction-design.md",
                "# Phase 3\n",
            )
            write_file(repo_root / "runs/current/artifacts/ux/navigation.md", "# Navigation\n")

            mocked_plan = {
                "phases": [
                    {
                        "id": "phase-3-ux-and-interaction-design",
                        "required_outputs": [
                            "runs/current/artifacts/ux/navigation.md",
                            "runs/current/evidence/ceo-phase-reviews/phase-3-ux-and-interaction-design.approved.md",
                        ],
                        "steps": [
                            {"id": "P3-UX-PACKAGE", "owners": ["frontend"], "requiredness": "required"},
                            {
                                "id": "P3-CEO-PHASE-REVIEW",
                                "owners": ["ceo"],
                                "requiredness": "required",
                                "outputs": {
                                    "artifacts": [
                                        "runs/current/evidence/ceo-phase-reviews/phase-3-ux-and-interaction-design.approved.md"
                                    ]
                                },
                            },
                        ],
                    }
                ]
            }
            mocked_state = {
                "steps": {
                    "P3-UX-PACKAGE": {"status": "pass"},
                    "P3-CEO-PHASE-REVIEW": {"status": "pending"},
                }
            }

            with unittest.mock.patch("recover_run_queue.compute_sdlc_state", return_value=(mocked_plan, mocked_state)):
                created = write_phase_ceo_review_notes(repo_root, "")

            self.assertEqual(len(created), 1)
            note_text = created[0].read_text(encoding="utf-8")
            self.assertIn("to: ceo", note_text)
            self.assertIn("phase-3-ux-and-interaction-design", note_text)
            self.assertIn("## Requested Outputs", note_text)
            self.assertIn("UX/UI quality", note_text)
            self.assertIn("runs/current/evidence/ceo-phase-reviews/phase-3-ux-and-interaction-design.approved.md", note_text)

    def test_select_recovery_targets_skips_architect_phase6_block_when_runtime_escalation_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            blocked_need = ArtifactNeed(
                role="architect",
                phase="phase-6-integration-review",
                path=repo_root / "runs/current/artifacts/architecture/integration-review.md",
                reason="status=blocked",
            )

            with unittest.mock.patch("recover_run_queue.collect_artifact_needs", return_value=[blocked_need]):
                with unittest.mock.patch("recover_run_queue.collect_completion_blocker_needs", return_value=[]):
                    with unittest.mock.patch(
                        "recover_run_queue.collect_runtime_environment_escalations",
                        return_value=[
                            RuntimeEnvironmentEscalation(
                                topic_slug="runtime-environment-recovery",
                                required_reads=(),
                                blocking_issues=(),
                                message_paths=(),
                            )
                        ],
                    ):
                        with unittest.mock.patch("recover_run_queue.role_pending", return_value=False):
                            with unittest.mock.patch("recover_run_queue.should_recover_phase", return_value=True):
                                targets = select_recovery_targets(repo_root)

            self.assertNotIn("architect", targets)

    def test_recovery_note_syncs_change_role_load_for_recovered_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_recovery_validation_baseline(repo_root)
            ensure_role_dirs(repo_root, "product_manager")

            change_id = "CR-test"
            role_load_path = repo_root / "runs/current/changes" / change_id / "role-loads/product_manager.yaml"
            write_file(
                role_load_path,
                "\n".join(
                    [
                        f"change_id: {change_id}",
                        "scope_profile: frontend-only",
                        "active: true",
                        "baseline_id: REL-test",
                        "read_artifacts:",
                        "  - runs/current/artifacts/product/user-stories.md",
                        "write_artifacts:",
                        "  - runs/current/artifacts/product/user-stories.md",
                        "read_app_paths: []",
                        "write_app_paths: []",
                        "verification_inputs: []",
                        "",
                    ]
                ),
            )

            needs = [
                ArtifactNeed(
                    role="product_manager",
                    phase="phase-7-product-acceptance",
                    path=repo_root / "runs/current/artifacts/product/acceptance-review.md",
                    reason="missing",
                )
            ]

            created = write_recovery_notes(repo_root, {"product_manager": needs}, change_id)
            self.assertEqual(len(created), 1)

            payload = yaml.safe_load(role_load_path.read_text(encoding="utf-8"))
            self.assertIn("runs/current/artifacts/product/acceptance-review.md", payload["read_artifacts"])
            self.assertIn("runs/current/artifacts/product/acceptance-review.md", payload["write_artifacts"])

    def test_recovery_note_syncs_change_role_load_for_recovered_verification_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_recovery_validation_baseline(repo_root)
            ensure_role_dirs(repo_root, "qa")

            change_id = "CR-test"
            role_load_path = repo_root / "runs/current/changes" / change_id / "role-loads/qa.yaml"
            write_file(
                role_load_path,
                "\n".join(
                    [
                        f"change_id: {change_id}",
                        "scope_profile: fullstack",
                        "active: true",
                        "baseline_id: REL-test",
                        "read_artifacts:",
                        f"  - runs/current/changes/{change_id}/request.md",
                        "write_artifacts: []",
                        "read_app_paths: []",
                        "write_app_paths: []",
                        "verification_inputs: []",
                        "",
                    ]
                ),
            )

            needs = [
                ArtifactNeed(
                    role="qa",
                    phase="phase-6-integration-review",
                    path=repo_root / f"runs/current/changes/{change_id}/verification/reference-fidelity-review.md",
                    reason="binding external UI reference fidelity review is not approved: status=draft",
                )
            ]

            created = write_recovery_notes(repo_root, {"qa": needs}, change_id)
            self.assertEqual(len(created), 1)

            payload = yaml.safe_load(role_load_path.read_text(encoding="utf-8"))
            self.assertIn(
                f"runs/current/changes/{change_id}/verification/reference-fidelity-review.md",
                payload["verification_inputs"],
            )

    def test_missing_docker_files_do_not_trigger_deployment_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_app_baseline(repo_root)
            write_required_phase6_evidence(repo_root)
            (repo_root / "app" / "Dockerfile").unlink()
            (repo_root / "app" / "docker-compose.yml").unlink()

            with unittest.mock.patch("recover_run_queue.collect_completion_blocker_needs", return_value=[]):
                targets = select_recovery_targets(repo_root)
            self.assertEqual(targets, {})

    def test_does_not_recover_while_initial_input_is_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/product/brief.md", "product_manager", "phase-1-product-definition")
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_file(repo_root / "runs/current/role-state/product_manager/inbox/INPUT.md", "# brief\n")

            targets = select_recovery_targets(repo_root)
            self.assertEqual(targets, {})

    def test_requeues_early_phase_missing_artifacts_by_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/product/brief.md", "product_manager", "phase-1-product-definition")
            write_template(repo_root / "specs/ux/iconography.md", "frontend", "phase-3-ux-and-interaction-design")
            write_template(repo_root / "specs/architecture/integration-review.md", "architect", "phase-6-integration-review")
            write_template(repo_root / "specs/product/acceptance-review.md", "product_manager", "phase-7-product-acceptance")

            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            with unittest.mock.patch("recover_run_queue.collect_completion_blocker_needs", return_value=[]):
                targets = select_recovery_targets(repo_root)

            self.assertIn("product_manager", targets)
            self.assertNotIn("frontend", targets)
            self.assertNotIn("architect", targets)

            product_paths = {need.path.relative_to(repo_root).as_posix() for need in targets["product_manager"]}
            self.assertIn("runs/current/artifacts/product/brief.md", product_paths)
            self.assertNotIn("runs/current/artifacts/product/acceptance-review.md", product_paths)

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/product/brief.md", "product_manager", "phase-1-product-definition")
            write_template(repo_root / "specs/ux/iconography.md", "frontend", "phase-3-ux-and-interaction-design")
            write_template(repo_root / "specs/architecture/integration-review.md", "architect", "phase-6-integration-review")
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_run_artifact(repo_root / "runs/current/artifacts/product/brief.md")
            write_run_artifact(repo_root / "runs/current/artifacts/ux/iconography.md")
            write_app_baseline(repo_root)
            write_required_phase6_evidence(repo_root)

            with unittest.mock.patch("recover_run_queue.collect_completion_blocker_needs", return_value=[]):
                targets = select_recovery_targets(repo_root)

            self.assertEqual(set(targets), {"architect"})
            architect_paths = {need.path.relative_to(repo_root).as_posix() for need in targets["architect"]}
            self.assertEqual(architect_paths, {"runs/current/artifacts/architecture/integration-review.md"})

    def test_recovery_waits_for_phase1_and_phase2_before_phase3_and_phase4(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/product/brief.md", "product_manager", "phase-1-product-definition")
            write_template(repo_root / "specs/architecture/overview.md", "architect", "phase-2-architecture-contract")
            write_template(repo_root / "specs/ux/iconography.md", "frontend", "phase-3-ux-and-interaction-design")
            write_template(repo_root / "specs/backend-design/model-design.md", "backend", "phase-4-backend-design-and-rules-mapping")
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            targets = select_recovery_targets(repo_root)
            self.assertEqual(set(targets), {"product_manager"})

            write_run_artifact(repo_root / "runs/current/artifacts/product/brief.md")
            targets = select_recovery_targets(repo_root)
            self.assertEqual(set(targets), {"architect"})

            write_run_artifact(repo_root / "runs/current/artifacts/architecture/overview.md")
            targets = select_recovery_targets(repo_root)
            self.assertEqual(set(targets), {"frontend", "backend"})

    def test_collect_completion_blocker_needs_skips_optional_business_rules_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            with unittest.mock.patch(
                "recover_run_queue.collect_blockers",
                return_value=[
                    {
                        "kind": "missing-generated-app-output",
                        "owner": "product_manager",
                        "phase": "phase-5-parallel-implementation",
                        "path": "app/BUSINESS_RULES.md",
                        "reason": "optional export omitted",
                    }
                ],
            ):
                needs = collect_completion_blocker_needs(repo_root)

            self.assertEqual(needs, [])

    def test_requeues_architect_for_ui_preview_review_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_app_baseline(repo_root)
            write_required_phase6_evidence(repo_root)
            write_file(
                repo_root / "runs/current/evidence/ui-previews/manifest.md",
                "\n".join(
                    [
                        "# UI Preview Manifest",
                        "",
                        "capture_status: captured",
                        "content_validation_status: pending-review",
                        "frontend_validation: approved",
                        "architect_validation: pending-review",
                        "product_manager_validation: pending-review",
                        "review_conclusion: pending-review",
                        "",
                    ]
                ),
            )
            write_file(repo_root / "runs/current/evidence/ui-previews/admin-entry.png", "fake image")

            with unittest.mock.patch(
                "recover_run_queue.collect_completion_blocker_needs",
                return_value=[
                    ArtifactNeed(
                        role="architect",
                        phase="phase-6-integration-review",
                        path=repo_root / "runs/current/evidence/ui-previews/manifest.md",
                        reason="content_validation_status=pending-review",
                    )
                ],
            ):
                targets = select_recovery_targets(repo_root)

            self.assertEqual(set(targets), {"architect"})
            architect_paths = {need.path.relative_to(repo_root).as_posix() for need in targets["architect"]}
            self.assertEqual(architect_paths, {"runs/current/evidence/ui-previews/manifest.md"})

    def test_requeues_backend_for_backend_source_validation_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_recovery_validation_baseline(repo_root)
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_app_baseline(repo_root)
            write_required_phase6_evidence(repo_root)
            write_file(
                repo_root / "runs/current/artifacts/backend-design/resource-exposure-policy.md",
                "| `Project` | yes |\n",
            )
            write_file(
                repo_root / "app/backend/src/my_app/fastapi_app.py",
                "\n".join(
                    [
                        "from fastapi import FastAPI",
                        "def create_app():",
                        '    return FastAPI(openapi_url="/jsonapi.json")',
                        "",
                    ]
                ),
            )
            write_file(repo_root / "app/backend/src/my_app/db.py", "from sqlalchemy import text\n")

            with unittest.mock.patch(
                "recover_run_queue.collect_completion_blocker_needs",
                return_value=[
                    ArtifactNeed(
                        role="backend",
                        phase="phase-5-parallel-implementation",
                        path=repo_root / "app/backend/src",
                        reason="backend-orm-safrs-audit-failed",
                        extra_reads=(
                            "playbook/task-bundles/backend-implementation.yaml",
                            "playbook/process/phases/phase-5-parallel-implementation.md",
                            "runs/current/artifacts/backend-design/resource-exposure-policy.md",
                        ),
                    )
                ],
            ):
                targets = select_recovery_targets(repo_root)

            self.assertEqual(set(targets), {"backend"})
            backend_paths = {need.path.relative_to(repo_root).as_posix() for need in targets["backend"]}
            self.assertEqual(backend_paths, {"app/backend/src"})
            backend_phases = {need.phase for need in targets["backend"]}
            self.assertEqual(backend_phases, {"phase-5-parallel-implementation"})

            created = write_recovery_notes(repo_root, targets, "test-change")
            self.assertEqual(len(created), 1)
            note = created[0].read_text(encoding="utf-8")
            self.assertIn("playbook/task-bundles/backend-implementation.yaml", note)
            self.assertIn("playbook/process/phases/phase-5-parallel-implementation.md", note)
            self.assertNotIn("playbook/task-bundles/integration-review.yaml", note)
            self.assertNotIn("playbook/process/phases/phase-6-integration-review.md", note)

    def test_acceptance_review_is_only_requeued_after_other_core_roles_are_quiescent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/product/acceptance-review.md", "product_manager", "phase-7-product-acceptance")
            write_template(repo_root / "specs/architecture/integration-review.md", "architect", "phase-6-integration-review")
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_run_artifact(repo_root / "runs/current/artifacts/architecture/integration-review.md")
            write_app_baseline(repo_root)
            write_required_phase6_evidence(repo_root)
            (repo_root / "runs/current/role-state/backend/inflight/todo.md").write_text("busy\n", encoding="utf-8")

            with unittest.mock.patch("recover_run_queue.collect_completion_blocker_needs", return_value=[]):
                targets = select_recovery_targets(repo_root)
            self.assertNotIn("product_manager", targets)

            (repo_root / "runs/current/role-state/backend/inflight/todo.md").unlink()
            with unittest.mock.patch("recover_run_queue.collect_completion_blocker_needs", return_value=[]):
                targets = select_recovery_targets(repo_root)
            self.assertIn("product_manager", targets)
            product_paths = {need.path.relative_to(repo_root).as_posix() for need in targets["product_manager"]}
            self.assertEqual(product_paths, {"runs/current/artifacts/product/acceptance-review.md"})

    def test_qa_review_is_only_requeued_after_acceptance_is_clear_and_other_roles_are_quiescent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_recovery_validation_baseline(repo_root)
            for role in ("product_manager", "architect", "frontend", "backend", "qa", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_app_baseline(repo_root)
            write_required_phase6_evidence(repo_root)
            write_run_artifact(repo_root / "runs/current/artifacts/product/acceptance-review.md", status="approved")

            qa_need = ArtifactNeed(
                role="qa",
                phase="phase-8-qa-pre-delivery-validation",
                path=repo_root / "runs/current/evidence/qa-delivery-review.md",
                reason="Story Live Coverage rows are incomplete",
            )

            (repo_root / "runs/current/role-state/frontend/inflight/todo.md").write_text("busy\n", encoding="utf-8")
            with unittest.mock.patch("recover_run_queue.collect_artifact_needs", return_value=[]):
                with unittest.mock.patch("recover_run_queue.collect_completion_blocker_needs", return_value=[qa_need]):
                    targets = select_recovery_targets(repo_root)
            self.assertNotIn("qa", targets)

            (repo_root / "runs/current/role-state/frontend/inflight/todo.md").unlink()
            with unittest.mock.patch("recover_run_queue.collect_artifact_needs", return_value=[]):
                with unittest.mock.patch("recover_run_queue.collect_completion_blocker_needs", return_value=[qa_need]):
                    targets = select_recovery_targets(repo_root)

            self.assertEqual(set(targets), {"qa"})
            qa_paths = {need.path.relative_to(repo_root).as_posix() for need in targets["qa"]}
            self.assertEqual(qa_paths, {"runs/current/evidence/qa-delivery-review.md"})

    def test_stalled_run_triage_creates_ceo_note_when_blockers_remain_but_no_worker_queue_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_recovery_validation_baseline(repo_root)
            for role in ("product_manager", "architect", "frontend", "backend", "qa", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            blockers = [
                {
                    "kind": "qa-review-coverage",
                    "owner": "qa",
                    "phase": "phase-8-qa-pre-delivery-validation",
                    "path": "runs/current/evidence/qa-delivery-review.md",
                    "reason": "QA review story US-007 is missing screenshot proof",
                }
            ]

            with unittest.mock.patch("recover_run_queue.collect_blockers", return_value=blockers):
                created = write_stalled_run_triage_notes(repo_root, "test-change")

            self.assertEqual(len(created), 1)
            note_text = created[0].read_text(encoding="utf-8")
            self.assertIn("to: ceo", note_text)
            self.assertIn("topic: stalled-run-triage", note_text)
            self.assertIn("no actionable worker inbox or inflight work remained", note_text)
            self.assertIn("runs/current/evidence/qa-delivery-review.md", note_text)

    def test_recovery_note_includes_phase_bundle_and_template_reads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_recovery_validation_baseline(repo_root)
            write_template(repo_root / "specs/ux/iconography.md", "frontend", "phase-3-ux-and-interaction-design")
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            targets = select_recovery_targets(repo_root)
            created = write_recovery_notes(repo_root, targets, "test-change")
            self.assertEqual(len(created), 1)

            note = created[0].read_text(encoding="utf-8")
            self.assertIn("playbook/task-bundles/ux-design.yaml", note)
            self.assertIn("playbook/process/phases/phase-3-ux-and-interaction-design.md", note)
            self.assertIn("specs/ux/README.md", note)
            self.assertIn("specs/ux/iconography.md", note)
            self.assertIn("runs/current/artifacts/ux/iconography.md", note)

    def test_phase5_gated_frontend_self_handoff_does_not_block_phase3_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_recovery_validation_baseline(repo_root)
            write_template(repo_root / "specs/product/brief.md", "product_manager", "phase-1-product-definition")
            write_template(repo_root / "specs/architecture/overview.md", "architect", "phase-2-architecture-contract")
            write_template(repo_root / "specs/ux/iconography.md", "frontend", "phase-3-ux-and-interaction-design")
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_run_artifact(repo_root / "runs/current/artifacts/product/brief.md")
            write_run_artifact(repo_root / "runs/current/artifacts/architecture/overview.md")
            write_run_artifact(repo_root / "runs/current/artifacts/architecture/capability-profile.md")
            write_run_artifact(repo_root / "runs/current/artifacts/architecture/load-plan.md")
            write_file(
                repo_root / "runs/current/role-state/frontend/inbox/20260406-123000-from-frontend-to-frontend-phase-4-implementation.md",
                "\n".join(
                    [
                        "from: frontend",
                        "to: frontend",
                        "topic: phase-4-frontend-implementation",
                        "gate_status: ready-for-handoff",
                        "",
                        "## Requested Outputs",
                        "- implement the frontend shell",
                    ]
                ),
            )

            with unittest.mock.patch("recover_run_queue.collect_completion_blocker_needs", return_value=[]):
                targets = select_recovery_targets(repo_root)

            self.assertEqual(set(targets), {"frontend"})
            frontend_paths = {need.path.relative_to(repo_root).as_posix() for need in targets["frontend"]}
            self.assertEqual(frontend_paths, {"runs/current/artifacts/ux/iconography.md"})

            created = write_recovery_notes(repo_root, targets, "")
            self.assertEqual(len(created), 1)
            self.assertTrue(
                (
                    repo_root
                    / "runs/current/role-state/frontend/processed/20260406-123000-from-frontend-to-frontend-phase-4-implementation.superseded-phase5-gated.md"
                ).exists()
            )

    def test_does_not_repeat_identical_recent_recovery_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_recovery_validation_baseline(repo_root)
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_app_baseline(repo_root)
            write_required_phase6_evidence(repo_root)
            write_file(
                repo_root / "runs/current/evidence/ui-previews/manifest.md",
                "\n".join(
                    [
                        "# UI Preview Manifest",
                        "",
                        "capture_status: captured",
                        "content_validation_status: reviewed",
                        "frontend_validation: approved",
                        "architect_validation: approved",
                        "product_manager_validation: pending-review",
                        "review_conclusion: pending-review",
                        "",
                    ]
                ),
            )
            write_file(repo_root / "runs/current/evidence/ui-previews/admin-entry.png", "fake image")

            targets = select_recovery_targets(repo_root)
            first_created = write_recovery_notes(repo_root, targets, "test-change")
            self.assertEqual(len(first_created), 1)

            second_created = write_recovery_notes(repo_root, targets, "test-change")
            self.assertEqual(second_created, [])

    def test_does_not_requeue_architect_runtime_bom_while_devops_queue_is_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/architecture/runtime-bom.md", "architect", "phase-2-architecture-contract")
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_run_artifact(repo_root / "runs/current/artifacts/architecture/runtime-bom.md", status="blocked")
            write_file(repo_root / "runs/current/role-state/devops/inbox/pending.md", "from: architect\nto: devops\n")

            targets = select_recovery_targets(repo_root)
            self.assertNotIn("architect", targets)


if __name__ == "__main__":
    unittest.main()
