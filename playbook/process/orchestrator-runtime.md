# Orchestrator Runtime

This file defines the expected runtime behavior of `run_playbook.sh`.

## Purpose

The orchestrator MUST:

- create a fresh local `runs/current/` from `runs/template/`
- seed the Product Manager inbox from the supplied brief
- process exactly one inbox message per Codex role invocation
- keep durable run state in artifacts, inbox traces, and role-local
  `context.md`
- use Codex session resume only as a speed and continuity layer
- log visible start and finish lines for every agent turn
- stop and surface a clear reason when the run becomes non-progressing

## Logging

For every Codex role invocation, the orchestrator MUST emit a visible log line
when the role starts.

That start log MUST include at least:

- timestamp
- runtime role
- inbox filename
- model
- whether the invocation is a fresh session or a resumed session

For every successful Codex role invocation, the orchestrator MUST emit a
visible finish log line.

That finish log MUST include at least:

- timestamp
- runtime role
- inbox filename
- a brief one-line summary

The summary SHOULD be taken from a final response line starting with
`Summary:`.

The orchestrator MUST persist its machine-readable evidence under
`runs/current/evidence/orchestrator/`.

## Session model

The orchestrator MUST maintain one Codex session record per runtime role in:

- `runs/current/evidence/orchestrator/sessions.json`

The role-local durable source of truth remains:

- owned files under `runs/current/artifacts/**`
- `runs/current/role-state/<role>/context.md`
- inbox and processed message traces

Codex session history MUST NOT be treated as authoritative run state.

If a stored session cannot be resumed cleanly, the orchestrator MAY discard the
stored session id for that role and start a fresh session.

## Model-selection rule

The orchestrator SHOULD default to the local Codex CLI model/account default.

It MAY accept explicit model overrides through environment variables such as:

- `FAST_MODEL`
- `MAIN_MODEL`
- `LONG_MODEL`

If those overrides are unset, the orchestrator MUST NOT force a hardcoded
model name that may be unsupported by the local Codex account.

If Codex emits a runtime error such as an unsupported model failure, the
orchestrator MUST stop and surface that real error instead of continuing into a
misleading inbox-state failure.

## Role-local AGENTS

At run reset, the orchestrator runtime MUST seed local role directories under
`runs/current/role-state/<role>/` with a role-local `AGENTS.md`.

Those role-local instructions MUST remain small and stable. They MUST define:

- role identity
- one-inbox-item-per-run behavior
- `context.md` update requirement
- processed-message archiving requirement
- cross-role edit prohibition

The role-local `AGENTS.md` is a stable persona layer. It MUST NOT replace the
real run state stored in artifacts or `context.md`.

## Writable-root rule

When the orchestrator starts Codex from a role-local runtime directory under
`runs/current/role-state/<role>/`, it MUST also grant writable access to the
role's owned sibling artifact and `app/` lanes.

At minimum, the orchestrator MUST grant:

- the role-local runtime directory
- the role-owned artifact directory under `runs/current/artifacts/`
- the role-owned `app/` subtree or root-owned app files
- the shared `runs/current/role-state/` tree for inbox handoffs

The orchestrator MUST NOT assume that starting Codex inside
`runs/current/role-state/<role>/` automatically grants write access to sibling
artifact or inbox paths.

## Phase-aware scheduling

The orchestrator MUST remain serial until the Phase 5 entry gate passes.

Before Phase 5:

- Product Manager runs in the main control lane
- Architect runs in the main control lane
- Frontend and Backend MAY process their own pre-Phase-5 inbox items, but only
  serially

After Phase 5:

- Frontend and Backend SHOULD run as long-lived background workers
- Product Manager and Architect MUST remain in the main control lane
- Frontend and Backend workers MUST process only their own oldest actionable
  inbox item per turn

Phase 5 readiness MUST be computed from run-owned artifact status, not guessed
from inbox activity.

## Stall detection

The orchestrator MUST detect a stalled run.

A run is stalled when all of the following are true:

- the completion checker still fails
- no actionable inbox items remain under `runs/current/role-state/*/inbox`
- no role turn completed useful work in the current control cycle

When a stall is detected, the orchestrator MUST:

- append a human-readable diagnosis to `runs/current/remarks.md`
- create a Product Manager inbox note describing the stall
- exit non-zero instead of sleeping forever

The Product Manager is the default owner of run-level stall triage. The
Product Manager MUST decide whether the run should be re-queued, corrected, or
reset.

## Parallel-write rule

Parallel implementation is allowed only because ownership is narrowed.

The orchestrator and validator MUST treat these `app/` ownership lanes as the
baseline:

- Product Manager -> `app/BUSINESS_RULES.md`
- Architect -> `app/README.md`
- Frontend -> `app/frontend/**`
- Backend -> `app/backend/**`, `app/rules/**`, `app/reference/admin.yaml`
- DevOps -> `app/.gitignore`, `app/Dockerfile`, `app/docker-compose.yml`,
  `app/nginx.conf`, `app/entrypoint.sh`, `app/install.sh`, `app/run.sh`

No role MAY silently write another role's `app/` lane.

## Prompt size rule

The orchestrator SHOULD use short path-based prompts by default.

Prompts SHOULD tell Codex:

- which single inbox item to process
- which files are required reads
- which writes are allowed
- that `context.md` must be updated
- that the inbox item must be moved to `processed/`
- that the final response must begin with `Summary:`

The orchestrator SHOULD NOT inline large blocks of playbook text on every
turn.
