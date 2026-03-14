# App Development Playbook

This playbook is now also exposed at:

- `../app_gen_playbook/`

Prefer the `app_gen_playbook/` name in new discussion and future external
references.

If a local filesystem still exposes `one_shot_gen/`, treat it as a temporary
compatibility alias only. New documentation and discussion MUST use
`app_gen_playbook/`.

This directory is now organized around the following top-level areas:

- `playbook/`
  Static role, process, phase, and compatibility instructions.
- `specs/`
  Generic artifact templates, durable technical contracts, and optional
  feature packs.
- `templates/`
  Copy-and-adapt core templates plus feature-gated template packs that mirror
  the generated `app/` shape.
- `runs/`
  Mutable execution state for the active run.
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
- keep generated implementation output under the local ignored `app/`

Agents MUST NOT collapse these layers together or broaden role reading
requirements without an explicit documented reason.

## Operator orientation

Use these files to understand the repository layout and the current run state:

1. [playbook/README.md](playbook/README.md)
2. [runs/README.md](runs/README.md)
3. [specs/README.md](specs/README.md)
4. [templates/README.md](templates/README.md)
5. [example/README.md](example/README.md)
6. [templates/app/project/README.app.md](templates/app/project/README.app.md)

## Fresh-run agent reading rule

For a fresh run, agents MUST start from:

1. [playbook/README.md](playbook/README.md)
2. [runs/current/README.md](runs/current/README.md)
3. the current role definition under `playbook/roles/`
4. the run-owned artifacts and owned specs required by that role

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

- [runs/current/README.md](runs/current/README.md)

The canonical run brief copy is:

- [runs/current/input.md](runs/current/input.md)

Run-local remarks and verification state live under:

- [runs/current/remarks.md](runs/current/remarks.md)
- [runs/current/artifacts/README.md](runs/current/artifacts/README.md)
- [runs/current/evidence/README.md](runs/current/evidence/README.md)

Artifact location rule:

- `specs/product/`, `specs/architecture/`, `specs/ux/`, and
  `specs/backend-design/` are generic template sources
- run-specific artifacts MUST be authored under `runs/current/artifacts/`
- `app/BUSINESS_RULES.md` MUST contain the generated-app copy of the approved
  business-rules catalog
- accepted artifacts MAY later be copied into local `app/docs/`
- `example/` is a preserved runnable example app generated from this playbook
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
