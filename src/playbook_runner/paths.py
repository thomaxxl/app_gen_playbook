from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlaybookPaths:
    repo_root: Path

    @property
    def scripts_root(self) -> Path:
        return self.repo_root / "scripts"

    @property
    def tools_root(self) -> Path:
        return self.repo_root / "tools"

    @property
    def app_root(self) -> Path:
        return self.repo_root / "app"

    @property
    def run_root(self) -> Path:
        return self.repo_root / "runs" / "current"

    @property
    def state_root(self) -> Path:
        return self.run_root / "role-state"

    @property
    def orchestrator_root(self) -> Path:
        return self.run_root / "orchestrator"

    @property
    def evidence_root(self) -> Path:
        return self.run_root / "evidence" / "orchestrator"

    @property
    def prompts_dir(self) -> Path:
        return self.evidence_root / "prompts"

    @property
    def jsonl_dir(self) -> Path:
        return self.evidence_root / "jsonl"

    @property
    def final_dir(self) -> Path:
        return self.evidence_root / "final"

    @property
    def logs_dir(self) -> Path:
        return self.evidence_root / "logs"

    @property
    def sessions_json(self) -> Path:
        return self.evidence_root / "sessions.json"

    @property
    def run_status_json(self) -> Path:
        return self.orchestrator_root / "run-status.json"

    @property
    def operator_action_required_md(self) -> Path:
        return self.orchestrator_root / "operator-action-required.md"

    @property
    def pause_requested_md(self) -> Path:
        return self.orchestrator_root / "pause-requested.md"

    @property
    def kill_requested_md(self) -> Path:
        return self.orchestrator_root / "kill-requested.md"

    @property
    def runner_pid_file(self) -> Path:
        return self.orchestrator_root / "runner.pid"

    @property
    def remarks_md(self) -> Path:
        return self.run_root / "remarks.md"

    @property
    def remarks_events_jsonl(self) -> Path:
        return self.run_root / "remarks-events.jsonl"

    @property
    def notes_md(self) -> Path:
        return self.run_root / "notes.md"

    @property
    def host_runtime_verification_md(self) -> Path:
        return self.run_root / "evidence" / "host-runtime-verification.md"

    @property
    def runtime_environment_json(self) -> Path:
        return self.orchestrator_root / "runtime-environment.json"

    @property
    def frontend_browser_proof_md(self) -> Path:
        return self.run_root / "evidence" / "frontend-browser-proof.md"

    @property
    def qa_delivery_review_md(self) -> Path:
        return self.run_root / "evidence" / "qa-delivery-review.md"

    @property
    def ceo_delivery_validation_md(self) -> Path:
        return self.run_root / "evidence" / "ceo-delivery-validation.md"

    @property
    def ceo_delivery_runtime_log(self) -> Path:
        return self.logs_dir / "ceo-delivery-app-run.log"

    @property
    def dashboard_root(self) -> Path:
        return self.repo_root / "run_dashboard"

    @property
    def dashboard_init(self) -> Path:
        return self.dashboard_root / "scripts" / "init_db.sh"

    @property
    def dashboard_sync(self) -> Path:
        return self.dashboard_root / "scripts" / "sync_once.sh"

    @property
    def dashboard_watch(self) -> Path:
        return self.dashboard_root / "scripts" / "watch_current_run.sh"

    def role_dir(self, runtime_role: str) -> Path:
        if runtime_role == "deployment":
            devops_dir = self.state_root / "devops"
            if devops_dir.is_dir():
                return devops_dir
        return self.state_root / runtime_role

    def ensure_core_dirs(self) -> None:
        for path in (
            self.run_root,
            self.state_root,
            self.orchestrator_root,
            self.evidence_root,
            self.prompts_dir,
            self.jsonl_dir,
            self.final_dir,
            self.logs_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
