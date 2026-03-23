from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from execution_scope import active_scope_gate_profiles


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ExecutionScopeTests(unittest.TestCase):
    def test_flat_change_policy_profiles_only_override_quality_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "playbook/routing/execution-scopes.yaml",
                "\n".join(
                    [
                        "frontend-only:",
                        "  iterative-change-run:",
                        "    gate_profiles:",
                        "      quality:",
                        "        - gate-quality-frontend-delta",
                        "      acceptance:",
                        "        - gate-acceptance-frontend-delta",
                        "      delivery:",
                        "        - gate-delivery",
                        "",
                    ]
                ),
            )
            write_file(
                repo_root / "runs/current/orchestrator/run-status.json",
                '{"mode":"iterative-change-run","change_id":"CR-1","scope_profile":"frontend-only"}\n',
            )
            write_file(
                repo_root / "runs/current/changes/CR-1/classification.yaml",
                "\n".join(
                    [
                        "scope_profile: frontend-only",
                        "active_policy_profiles:",
                        "  - gate-quality-frontend-delta",
                        "",
                    ]
                ),
            )

            self.assertEqual(
                active_scope_gate_profiles(repo_root, "quality"),
                ["gate-quality-frontend-delta"],
            )
            self.assertEqual(
                active_scope_gate_profiles(repo_root, "acceptance"),
                ["gate-acceptance-frontend-delta"],
            )
            self.assertEqual(
                active_scope_gate_profiles(repo_root, "delivery"),
                ["gate-delivery"],
            )

    def test_gate_mapped_change_policy_profiles_are_respected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "playbook/routing/execution-scopes.yaml",
                "\n".join(
                    [
                        "frontend-only:",
                        "  iterative-change-run:",
                        "    gate_profiles:",
                        "      quality:",
                        "        - gate-quality-frontend-delta",
                        "      acceptance:",
                        "        - gate-acceptance-frontend-delta",
                        "",
                    ]
                ),
            )
            write_file(
                repo_root / "runs/current/orchestrator/run-status.json",
                '{"mode":"iterative-change-run","change_id":"CR-2","scope_profile":"frontend-only"}\n',
            )
            write_file(
                repo_root / "runs/current/changes/CR-2/classification.yaml",
                "\n".join(
                    [
                        "scope_profile: frontend-only",
                        "active_policy_profiles:",
                        "  quality:",
                        "    - gate-quality-frontend-delta",
                        "  acceptance:",
                        "    - gate-acceptance-frontend-delta",
                        "",
                    ]
                ),
            )

            self.assertEqual(
                active_scope_gate_profiles(repo_root, "quality"),
                ["gate-quality-frontend-delta"],
            )
            self.assertEqual(
                active_scope_gate_profiles(repo_root, "acceptance"),
                ["gate-acceptance-frontend-delta"],
            )


if __name__ == "__main__":
    unittest.main()
