from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def normalize_runtime_env(raw_value: str) -> str:
    normalized = raw_value.strip().lower()
    if normalized == "sandbox":
        return "sandbox"
    return "host"


def normalize_agent_backend(raw_value: str) -> str:
    normalized = raw_value.strip().lower()
    aliases = {
        "": "goose_codex_bridge",
        "codex": "codex_exec_legacy",
        "codex_exec": "codex_exec_legacy",
        "codex_exec_legacy": "codex_exec_legacy",
        "legacy": "codex_exec_legacy",
        "goose": "goose_codex_bridge",
        "goose_codex": "goose_codex_bridge",
        "goose_codex_bridge": "goose_codex_bridge",
    }
    return aliases.get(normalized, "goose_codex_bridge")


@dataclass(frozen=True)
class ModelConfig:
    fast: str
    main: str
    long: str
    product_manager: str
    architect: str
    frontend: str
    backend: str
    qa: str
    deployment: str
    ceo: str
    reasoning_effort: str


@dataclass(frozen=True)
class RunnerConfig:
    repo_root: Path
    poll_seconds: int
    lease_seconds: int
    timeout_seconds: int
    runtime_env: str
    auto_start_app: bool
    enable_parallel_workers: bool
    models: ModelConfig
    agent_backend: str = "goose_codex_bridge"
    goose_provider: str = "chatgpt_codex"
    allow_backend_migration: bool = False

    @classmethod
    def from_env(cls, repo_root: Path) -> "RunnerConfig":
        fast = os.getenv("FAST_MODEL", "")
        main = os.getenv("MAIN_MODEL", "gpt-5.4")
        long_model = os.getenv("LONG_MODEL", "gpt-5.3-codex-spark")
        architect = os.getenv("ARCHITECT_MODEL", main)
        frontend = os.getenv("FRONTEND_MODEL", long_model)
        backend = os.getenv("BACKEND_MODEL", frontend)
        qa = os.getenv("QA_MODEL", main)
        deployment = os.getenv("DEPLOYMENT_MODEL", frontend)
        ceo = os.getenv("CEO_MODEL", architect)
        product_manager = os.getenv("PRODUCT_MANAGER_MODEL", fast or "gpt-5.4")
        models = ModelConfig(
            fast=fast,
            main=main,
            long=long_model,
            product_manager=product_manager,
            architect=architect,
            frontend=frontend,
            backend=backend,
            qa=qa,
            deployment=deployment,
            ceo=ceo,
            reasoning_effort=os.getenv("REASONING_EFFORT", "high"),
        )
        return cls(
            repo_root=repo_root,
            poll_seconds=int(os.getenv("POLL_SECONDS", "1")),
            lease_seconds=int(os.getenv("LEASE_SECONDS", "600")),
            timeout_seconds=int(os.getenv("CODEX_COMMAND_TIMEOUT_SECONDS", "1500")),
            runtime_env=normalize_runtime_env(os.getenv("PLAYBOOK_RUNTIME_ENV", "host")),
            auto_start_app=os.getenv("PLAYBOOK_AUTO_START_APP", "1") == "1",
            enable_parallel_workers=os.getenv("PLAYBOOK_ENABLE_PARALLEL_WORKERS", "0") == "1",
            models=models,
            agent_backend=normalize_agent_backend(os.getenv("PLAYBOOK_AGENT_BACKEND", "goose_codex_bridge")),
            goose_provider=os.getenv("PLAYBOOK_GOOSE_PROVIDER", os.getenv("GOOSE_PROVIDER", "chatgpt_codex")).strip()
            or "chatgpt_codex",
            allow_backend_migration=os.getenv("PLAYBOOK_ALLOW_AGENT_BACKEND_MIGRATION", "0") == "1",
        )
