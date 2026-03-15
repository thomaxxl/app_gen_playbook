# App Development Playbook

`app_gen_playbook` is a repository for generating SAFRS-based admin
applications through a structured multi-role workflow.

It is primarily intended for:

- maintainers of the playbook
- operators running a new app-generation pass
- reviewers trying to understand how generated apps are supposed to be built
- new contributors who need a high-level map before reading the detailed
  process and contract files

If you are an automated agent, read [AGENTS.md](AGENTS.md) instead of relying
on this file for execution rules.

## What This Repository Contains

- `playbook/`
  The process layer: roles, phases, read sets, routing manifests, and
  orchestration rules.
- `specs/`
  The durable contract layer: product, architecture, UX, backend-design, core
  technical contracts, and optional feature packs.
- `templates/`
  The literal copy-and-adapt file templates used to materialize a generated
  application.
- `scripts/`
  Operator entrypoints such as the playbook runner and local cleanup helpers.
- `tools/`
  Helper scripts used by the orchestrator and by maintainers.
- `runs/`
  The run workspace model.
  `runs/template/` is the tracked starter.
  `runs/current/` is the local active run created from that starter.
- `example/`
  A preserved runnable example app generated from this playbook.
- `app/`
  The local ignored generated-app working tree for the active run.
- `scripts/run_playbook.sh`
  The top-level orchestrator entrypoint for a new run.
- `scripts/clean.sh`
  Cleans local `runs/current/` and `app/` without touching tracked starter or
  example content.
- `scripts/monitor.sh`
  Tails the raw per-turn Codex event streams under
  `runs/current/evidence/orchestrator/jsonl/`.

## Repository Model

This repository is intentionally segmented:

- human/process instructions live under `playbook/`
- technical contracts live under `specs/contracts/`
- optional capability packs live under `specs/features/`
- literal implementation snippets live under `templates/`
- mutable run state lives under `runs/current/`
- generated application output lives under local `app/`

That separation is part of the design. It keeps the playbook readable for
humans and keeps agent context bounded during automated runs.

## Typical Workflow

For a new run:

1. Prepare a short input brief as markdown.
2. Start the orchestrator:

```bash
./scripts/run_playbook.sh path/to/input.md
```

3. The orchestrator creates local `runs/current/`, seeds the Product Manager
   inbox, and advances the run through the defined roles.
   If the run appears stalled, the orchestrator may invoke the dormant CEO
   recovery role to inspect progress and restore forward motion.
4. The generated app is built locally under `app/`.
5. A preserved runnable reference remains available under `example/`.

The orchestrator keeps per-role evidence under `runs/current/evidence/` and
per-role mutable state under `runs/current/role-state/`.

If you want to watch the raw Codex subprocess output live while the run is
active:

```bash
./scripts/monitor.sh
```

That monitor prints all current and future `*.events.jsonl` streams with
filename prefixes, including parallel role turns.

For authoritative iteration on an existing app:

```bash
./scripts/run_playbook.sh --mode iterate path/to/change_request.md
```

For interrupted-run continuation:

```bash
./scripts/run_playbook.sh --resume
```

## Key Files To Read Next

For human orientation:

1. [playbook/index.md](playbook/index.md)
2. [playbook/README.md](playbook/README.md)
3. [runs/README.md](runs/README.md)
4. [specs/README.md](specs/README.md)
5. [templates/README.md](templates/README.md)
6. [example/README.md](example/README.md)

For generated-app shape:

1. [templates/app/project/README.app.md](templates/app/project/README.app.md)
2. [templates/app/project/install.sh.md](templates/app/project/install.sh.md)
3. [templates/app/project/run.sh.md](templates/app/project/run.sh.md)

## Important Conventions

- `app/` is local and gitignored. It is created when a run starts.
- `runs/current/` is local run state, not committed playbook source.
- `example/` is a proof/reference app, not the source of truth for contracts.
- `specs/product/`, `specs/architecture/`, `specs/ux/`, and
  `specs/backend-design/` are template sources; run-specific artifacts belong
  under `runs/current/artifacts/`.
- Changes to the playbook repository itself are expected to be committed in
  git.

## Scope And Fit

This playbook currently fits best when the target app is a modest SAFRS admin
application with:

- a limited number of main resources
- a React-admin frontend
- a SAFRS backend
- SQLite-first runtime assumptions
- a manageable set of business rules and custom pages

It can be adapted to larger or more complex domains, but that usually requires
more artifact work, more explicit architectural decisions, and less reuse of
the starter templates.
