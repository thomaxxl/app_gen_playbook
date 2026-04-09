from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from playbook_runner.cli import adopt_pinned_backend_on_resume
from playbook_runner.config import RunnerConfig


class PlaybookRunnerCliTests(unittest.TestCase):
    def test_runner_config_defaults_to_goose_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            with patch.dict(os.environ, {}, clear=True):
                config = RunnerConfig.from_env(repo_root)
            self.assertEqual(config.agent_backend, "goose_codex_bridge")

    def test_resume_adopts_recorded_backend_when_backend_env_is_unset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            runtime_path = repo_root / "runs" / "current" / "orchestrator" / "runtime-environment.json"
            runtime_path.parent.mkdir(parents=True, exist_ok=True)
            runtime_path.write_text(
                json.dumps({"agent_backend": "codex_exec_legacy"}) + "\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                adopt_pinned_backend_on_resume(repo_root, resume=True)
                self.assertEqual(os.environ.get("PLAYBOOK_AGENT_BACKEND"), "codex_exec_legacy")

    def test_resume_does_not_override_explicit_backend_choice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            runtime_path = repo_root / "runs" / "current" / "orchestrator" / "runtime-environment.json"
            runtime_path.parent.mkdir(parents=True, exist_ok=True)
            runtime_path.write_text(
                json.dumps({"agent_backend": "codex_exec_legacy"}) + "\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"PLAYBOOK_AGENT_BACKEND": "goose_codex_bridge"}, clear=True):
                adopt_pinned_backend_on_resume(repo_root, resume=True)
                self.assertEqual(os.environ.get("PLAYBOOK_AGENT_BACKEND"), "goose_codex_bridge")


if __name__ == "__main__":
    unittest.main()
