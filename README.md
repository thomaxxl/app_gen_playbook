# App Development Playbook

This playbook is now also exposed at:

- `../app_gen_playbook/`

Prefer the `app_gen_playbook/` name in new discussion and future external
references.

If a local filesystem still exposes `one_shot_gen/`, treat it as a temporary
compatibility alias only. New documentation and discussion MUST use
`app_gen_playbook/`.

This directory is now organized around the following top-level areas:

- `run_playbook.sh`
  Top-level sequential orchestrator for a new playbook run.
- `AGENTS.md`
  Small stable repo-wide execution rules for orchestrated role runs.
- `playbook/`
  Static role, process, phase, and compatibility instructions.
- `specs/`
  Generic artifact templates, durable technical contracts, and optional
  feature packs.
- `templates/`
  Copy-and-adapt core templates plus feature-gated template packs that mirror
  the generated `app/` shape.
- `tools/`
  Helper scripts used by the orchestrator for run reset, prompt building,
  diff validation, and completion checks.
- `runs/`
  Tracked neutral run template plus the local active run workspace.
- `example/`
  A cleaned preserved example generated from this playbook.
- `app/`
  A local ignored generated-application working tree created when a run starts.
- this `README.md`
  The top-level index.

Role note:

- the canonical optional packaging role is now `playbook/roles/devops.md`
- `playbook/roles/deployment.md` remains only as a compatibility alias

## Version control rule

Changes to this playbook repository MUST be committed in git.

Agents MUST NOT leave playbook edits uncommitted at the end of a playbook
maintenance task unless the user explicitly asks for an uncommitted state.

## Segmentation preservation rule

Playbook segmentation exists to avoid context overload during agent execution.

When updating the playbook, agents MUST preserve and reinforce that
segmentation:

- keep static process instructions under `playbook/`
- keep durable contracts under `specs/contracts/`
- keep optional capability packs under `specs/features/`
- keep literal code templates under `templates/`
- keep mutable run state under `runs/current/`
  while keeping the tracked neutral starter under `runs/template/`
- keep generated implementation output under the local ignored `app/`

Agents MUST NOT collapse these layers together or broaden role reading
requirements without an explicit documented reason.

## Operator orientation

Use these files to understand the repository layout and the current run state:

1. [run_playbook.sh](run_playbook.sh)
2. [playbook/index.md](playbook/index.md)
3. [playbook/README.md](playbook/README.md)
4. [runs/README.md](runs/README.md)
5. [specs/README.md](specs/README.md)
6. [templates/README.md](templates/README.md)
7. [example/README.md](example/README.md)
8. [templates/app/project/README.app.md](templates/app/project/README.app.md)

## Orchestrated run entrypoint

Use the repository runner for a new serial inbox-driven run:

```bash
./run_playbook.sh path/to/input.md
```

This seeds `runs/current/`, creates the Product Manager `INPUT.md`, and then
processes one inbox message per role per pass until the formal completion
checker passes or a role invocation fails.

The orchestrator now also:

- logs every role start and finish with a brief one-line summary
- keeps one resume-capable Codex session per runtime role
- switches to parallel Frontend and Backend workers only after the Phase 5
  entry gate passes

## Fresh-run agent reading rule

For a fresh run, agents MUST start from:

1. [playbook/index.md](playbook/index.md)
2. [playbook/summaries/global-core.md](playbook/summaries/global-core.md)
3. [playbook/summaries/process-core.md](playbook/summaries/process-core.md)
4. the current role summary under `playbook/summaries/roles/`
5. the current role Tier 1 read set under `playbook/process/read-sets/`
6. the current task bundle under `playbook/task-bundles/`
7. local `runs/current/` after it has been created from `runs/template/`
8. the minimum run-owned artifacts and enabled feature packs required by that
   task bundle

For a fresh run, agents MUST NOT use `example/` or `app/` as product or
architecture inputs unless the task explicitly requests:

- example comparison
- app-only maintenance
- playbook maintenance

## Complexity envelope

This playbook currently fits best when the target app stays within a modest
admin-app shape:

- a small number of core resources
- one or a few reference resources
- limited LogicBank rules
- one or a few custom pages
- SQLite bootstrap data

It MAY be adapted to larger domains, but the operator SHOULD expect more
manual artifact work and non-starter template substitution.

## Run-local files

The active run root is:

- local `runs/current/`

The tracked neutral starter is:

- [runs/template/README.md](runs/template/README.md)

The canonical run brief copy is:

- local `runs/current/input.md`

Run-local remarks and verification state live under the local active run at:

- local `runs/current/remarks.md`
- local `runs/current/artifacts/`
- local `runs/current/evidence/`

Artifact location rule:

- `specs/product/`, `specs/architecture/`, `specs/ux/`, and
  `specs/backend-design/` are generic template sources
- run-specific artifacts MUST be authored under `runs/current/artifacts/`
- `app/BUSINESS_RULES.md` MUST contain the generated-app copy of the approved
  business-rules catalog
- accepted artifacts MAY later be copied into local `app/docs/`
- `example/` is a preserved runnable example app generated from this playbook
- `example/` is proof that the playbook can generate a runnable app; it is
  not a normative source for runtime, dependency, or packaging decisions
- an explicit app-only maintenance pass MAY update local `app/` while leaving
  `runs/current/` unchanged; see `playbook/process/playbook-execution-outputs.md`

Generated-app working-tree rule:

- `app/` MUST be gitignored
- `app/` MUST be created locally when a run starts
- `app/` MUST NOT be treated as committed playbook source
- for a fresh run, the Product Manager SHOULD create local `app/` after intake
  setup so later roles have a stable output root
- the generated app itself MUST still include its own root `.gitignore`,
  `Dockerfile`, and `docker-compose.yml` so it can be moved into its own repo
  or packaged directly

Capability-loading rule:

- optional capabilities MUST be controlled by
  `runs/current/artifacts/architecture/capability-profile.md`
- role-scoped reading and copy scope MUST be controlled by
  `runs/current/artifacts/architecture/load-plan.md`
- disabled or undecided feature packs MUST NOT be loaded or copied into `app/`
- capability segmentation is a loading/copy/activation rule first; it does not
  imply zero dormant runtime footprint unless the relevant feature pack says so
- feature-pack maturity, owner roles, and allowed activation status are
  cataloged in `specs/features/catalog.md`

## Retrieval-first rule

This repository is a retrieval library for agents, not a monolithic document
set for preload.

Agents MUST prefer:

1. summary files
2. read-set manifests
3. task bundles
4. the minimum run-owned artifacts needed for the current task
5. enabled feature-pack contracts only

Agents MUST NOT start by scanning whole directories "just in case".
