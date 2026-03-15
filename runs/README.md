# Runs

This directory distinguishes:

- `template/`
  The tracked neutral starter workspace
- local `current/`
  The active run workspace created from `template/`

Rules:

- `template/` MUST stay neutral and reusable
- local `current/` MUST be created from `template/` at run start
- generated apps and run-owned artifacts MUST NOT treat `template/` as a real
  prior project
- `template/` SHOULD contain the neutral starter gating files needed to create
  `current/` without guesswork

The default orchestrated path is:

```bash
./scripts/run_playbook.sh path/to/input.md
```

Other supported paths:

```bash
./scripts/run_playbook.sh --mode iterate path/to/change_request.md
./scripts/run_playbook.sh --mode hotfix path/to/hotfix.md
./scripts/run_playbook.sh --resume
./scripts/run_playbook.sh --resume --role backend
```

That runner resets local `runs/current/` from `template/` before seeding the
next real brief when the mode is `new`.

During execution, the orchestrator also maintains:

- local `runs/current/evidence/orchestrator/sessions.json`
- local `runs/current/evidence/orchestrator/logs/orchestrator.log`
- local role-specific `AGENTS.md` files under `runs/current/role-state/`
- local `runs/current/role-state/*/inflight/`
- local `runs/current/orchestrator/run-status.json`
- local `runs/current/orchestrator/workers/*.json`
