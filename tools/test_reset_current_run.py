from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reset_current_run import reset_current_run


def write_template(path: Path, target: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# `{target}`\n\n```txt\n{body}```\n", encoding="utf-8")


class ResetCurrentRunTests(unittest.TestCase):
    def test_seeds_generated_app_subtree_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            template_dir = repo_root / "runs" / "template"
            (template_dir / "artifacts" / "architecture").mkdir(parents=True)
            (template_dir / "role-state").mkdir(parents=True)
            (template_dir / "README.md").write_text("# template\n", encoding="utf-8")
            write_template(repo_root / "templates" / "app" / "project" / ".gitignore.md", "app/.gitignore", "root-ignore\n")
            write_template(repo_root / "templates" / "app" / "project" / "install.sh.md", "app/install.sh", "#!/usr/bin/env bash\necho install\n")
            write_template(repo_root / "templates" / "app" / "project" / "run.sh.md", "app/run.sh", "#!/usr/bin/env bash\necho run\n")
            write_template(repo_root / "templates" / "app" / "project" / "README.app.md", "app/README.md", "# App\n")
            write_template(repo_root / "templates" / "app" / "frontend" / "package.json.md", "frontend/package.json", "{\n  \"name\": \"seeded\"\n}\n")
            write_template(repo_root / "templates" / "app" / "frontend" / "vite.config.ts.md", "frontend/vite.config.ts", "export default {};\n")

            reset_current_run(repo_root)

            self.assertTrue((repo_root / "app").is_dir())
            self.assertTrue((repo_root / "app" / "frontend").is_dir())
            self.assertTrue((repo_root / "app" / "backend").is_dir())
            self.assertTrue((repo_root / "app" / "rules").is_dir())
            self.assertTrue((repo_root / "app" / "reference").is_dir())
            self.assertTrue((repo_root / "runs" / "current" / "role-state" / "devops").is_dir())
            self.assertTrue((repo_root / "runs" / "current" / "role-state" / "qa").is_dir())
            self.assertTrue((repo_root / "runs" / "current" / "role-state" / "orchestrator" / "inbox").is_dir())
            self.assertTrue((repo_root / "runs" / "current" / "role-state" / "orchestrator" / "processed").is_dir())
            self.assertTrue((repo_root / "runs" / "current" / "remarks.md").is_file())
            self.assertTrue((repo_root / "runs" / "current" / "notes.md").is_file())
            ceo_agents = (repo_root / "runs" / "current" / "role-state" / "ceo" / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("repair the current blocker even in local playbook runtime files when necessary", ceo_agents)
            self.assertIn("validate delivery through scripts/run_playbook.sh --ceo-delivery-validate before final approval", ceo_agents)
            self.assertIn("so the orchestrator can curate runs/current/remarks.md", ceo_agents)
            self.assertIn("keeping only compact durable context relevant to future turns or future runs", ceo_agents)
            qa_agents = (repo_root / "runs" / "current" / "role-state" / "qa" / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("independently validate the delivered app before CEO approval", qa_agents)
            self.assertEqual((repo_root / "app" / ".gitignore").read_text(encoding="utf-8"), "root-ignore")
            self.assertEqual((repo_root / "app" / "README.md").read_text(encoding="utf-8"), "# App")
            self.assertIn('"name": "seeded"', (repo_root / "app" / "frontend" / "package.json").read_text(encoding="utf-8"))
            self.assertEqual((repo_root / "app" / "frontend" / "vite.config.ts").read_text(encoding="utf-8"), "export default {};")
            self.assertTrue((repo_root / "app" / "install.sh").stat().st_mode & 0o111)
            self.assertTrue((repo_root / "app" / "run.sh").stat().st_mode & 0o111)

    def test_seeds_symlinked_app_workspace_when_target_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir(parents=True)
            (repo_root / ".git").mkdir()
            target_root = Path(tmp) / "workspace" / "app"
            (repo_root / "app").symlink_to(target_root)
            template_dir = repo_root / "runs" / "template"
            (template_dir / "artifacts" / "architecture").mkdir(parents=True)
            (template_dir / "role-state").mkdir(parents=True)
            (template_dir / "README.md").write_text("# template\n", encoding="utf-8")
            write_template(repo_root / "templates" / "app" / "project" / ".gitignore.md", "app/.gitignore", "root-ignore\n")
            write_template(repo_root / "templates" / "app" / "project" / "install.sh.md", "app/install.sh", "#!/usr/bin/env bash\necho install\n")
            write_template(repo_root / "templates" / "app" / "project" / "run.sh.md", "app/run.sh", "#!/usr/bin/env bash\necho run\n")
            write_template(repo_root / "templates" / "app" / "project" / "README.app.md", "app/README.md", "# App\n")
            write_template(repo_root / "templates" / "app" / "frontend" / "package.json.md", "frontend/package.json", "{\n  \"name\": \"seeded\"\n}\n")

            reset_current_run(repo_root)

            self.assertTrue((repo_root / "app").is_symlink())
            self.assertTrue(target_root.is_dir())
            self.assertTrue((target_root / "frontend").is_dir())
            self.assertTrue((target_root / "backend").is_dir())
            self.assertEqual((target_root / ".gitignore").read_text(encoding="utf-8"), "root-ignore")
            self.assertIn('"name": "seeded"', (target_root / "frontend" / "package.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
