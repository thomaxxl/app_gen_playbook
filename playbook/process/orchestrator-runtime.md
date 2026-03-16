# Orchestrator Runtime

This file defines the expected runtime behavior of `scripts/run_playbook.sh`.

## Purpose

The orchestrator MUST:

- support `new-full-run`, `iterative-change-run`, `app-only-hotfix`, and
  `--resume`
- create a fresh local `runs/current/` from `runs/template/` for a new full
  run
- seed the Product Manager inbox from the supplied brief or change request
- process exactly one inbox message per Codex role invocation
- keep durable run state in artifacts, inbox traces, and role-local
  `context.md`
- use Codex session resume only as a speed and continuity layer
- log visible start and finish lines for every agent turn
- stop and surface a clear reason when the run becomes non-progressing
- keep the CEO role dormant unless a stall candidate is detected or the
  operator explicitly targets the CEO role
- validate handoff inputs before dispatching the receiver
- surface canonical output filenames to the active role at prompt time when
  the current phase or task bundle implies them
- refuse to declare completion while required run-owned artifacts remain
  missing, stub, or blocked, or while required generated-app outputs under
  `app/` are still absent

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

The raw stdout and stderr stream from each `codex exec` invocation MUST be
captured in the matching per-turn JSONL file under:

- `runs/current/evidence/orchestrator/jsonl/*.events.jsonl`

Recovery actions SHOULD be recorded in:

- `runs/current/evidence/orchestrator/recovery-log.md`

The repository SHOULD provide a simple operator monitor that can tail all
current and newly-created per-turn JSONL files concurrently.

Repository snapshotting and diff validation MUST treat repo-local symlink
entries by their lexical path inside the repository. The validator MUST NOT
dereference a repo-local symlink target before computing repo-relative paths,
because local virtualenv or tool-shim entries may resolve outside the repo.

When the orchestrator starts Codex in the background and uses `-` to request a
prompt from standard input, it MUST redirect the prompt file into the Codex
process explicitly. It MUST NOT rely on inherited stdin after backgrounding the
Codex subprocess.

Every maintained shell entrypoint under `scripts/` MUST continue to pass
`bash -n`. Playbook validation MUST treat shell-syntax regressions as release
blocking, because a broken runner cannot self-recover once the shell parser
fails before startup.

## Session model

The orchestrator MUST maintain one Codex session record per runtime role in:

- `runs/current/evidence/orchestrator/sessions.json`

The role-local durable source of truth remains:

- owned files under `runs/current/artifacts/**`
- `runs/current/role-state/<role>/context.md`
- inbox, inflight, and processed message traces

Codex session history MUST NOT be treated as authoritative run state.

If a stored session cannot be resumed cleanly, the orchestrator MAY discard the
stored session id for that role and start a fresh session.

On the currently installed Codex CLI, `codex exec resume` MUST NOT be invoked
with `--cd` or `--add-dir`. Fresh sessions MAY use those flags to establish
the role-local workspace and writable roots, but resumed sessions MUST rely on
the persisted session context instead.

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

The optional DevOps lane uses the runtime role token `deployment`, but its
physical run-state directory MUST be:

- `runs/current/role-state/devops/`

The orchestrator MUST continue to recognize legacy `runs/current/role-state/deployment/`
state if it already exists in an interrupted run, but new runs MUST seed and
prefer the `devops/` directory.

Those role-local instructions MUST remain small and stable. They MUST define:

- role identity
- one-inbox-item-per-run behavior
- `context.md` update requirement
- processed-message archiving requirement
- cross-role edit prohibition

The role-local `AGENTS.md` is a stable persona layer. It MUST NOT replace the
real run state stored in artifacts or `context.md`.

## Claimed work

Each role runtime directory MUST include:

- `inbox/`
- `inflight/`
- `processed/`

The orchestrator MUST move a claimed work item from `inbox/` to `inflight/`
before the Codex turn starts.

The role turn is complete only when the claimed item leaves `inflight/` and is
archived to `processed/`.

If the orchestrator synthesizes a recovery inbox note for a missing canonical
artifact, that queued note MUST count as useful progress for the current
control cycle. The orchestrator MUST NOT declare a stall in the same cycle
that it successfully re-queued recovery work.

The repository MAY also use `runs/current/role-state/orchestrator/inbox/` for
exception-routing notes that are not normal role handoffs. The orchestrator
runtime itself MUST process that inbox. It MUST NOT leave those notes counted
as actionable work without routing them onward.

When an orchestrator exception note is received, the orchestrator SHOULD
archive it under `runs/current/role-state/orchestrator/processed/` and convert
it into an explicit CEO intervention note unless a more specific automatic
recovery path is defined.

Before claiming work for any runtime role, the orchestrator MUST quarantine
duplicate queue traces. If a message basename already exists in `processed/`,
an `inflight/` or `inbox/` copy of that same basename MUST be archived as a
duplicate trace instead of being re-run. The orchestrator MUST preserve the
duplicate file as evidence and MUST NOT misclassify that condition as a role
implementation failure.

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

The local generated-app workspace MUST also contain the role-owned subtree
roots before implementation starts. At minimum, a new run MUST seed:

- `app/frontend/`
- `app/backend/`
- `app/rules/`
- `app/reference/`

The orchestrator MUST NOT rely on `--add-dir` for a non-existent path and then
expect the role to create that path later.

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
- CEO MUST run immediately when a CEO inbox note already exists
- Frontend and Backend workers MUST process only their own oldest actionable
  inbox item per turn

The orchestrator MUST NOT start a long-lived background worker through command
substitution or any other construct that runs the starter in a subshell and
captures its stdout. In Bash, that pattern can cause the shell to wait on the
background worker before the substitution completes, which blocks the main
control lane. If the main control lane is blocked, normal liveness checks and
CEO stall intervention cannot run.

The orchestrator MUST capture worker PIDs through a non-subshell path, such as
an explicit shared variable set by the worker-start helper.

Phase 5 readiness MUST be computed from run-owned artifact status, not guessed
from inbox activity.

## Resume behavior

When `--resume` is used, the orchestrator MUST:

- avoid resetting `runs/current/`
- inspect existing worker state and inflight items
- prefer continuing inflight work over claiming a new inbox item
- resume a stored Codex session only when the inflight state is still
  consistent
- rebuild from repo state when session continuity is missing or unsafe
- run a queue-recovery pass before continuing normal scheduling when
  completion still fails

If a resume attempt fails and the orchestrator falls back to a fresh turn, it
SHOULD preserve the failed resume JSONL stream before overwriting the normal
per-turn evidence files. The operator MUST be able to inspect the actual
resume failure instead of losing it to the fresh retry path.

## Canonical-artifact recovery

If completion still fails because canonical run-owned artifacts are missing or
still `status: stub`, the orchestrator SHOULD synthesize targeted recovery
handoffs instead of waiting for the queue to drain permanently.

The recovery pass MUST:

- remain dormant while the initial Product Manager intake item
  `runs/current/role-state/product_manager/{inbox,inflight}/INPUT.md` still
  exists
- pre-validate every synthesized recovery note before counting it as useful
  progress
- stop immediately with a clear orchestrator error if it generates an invalid
  recovery note, instead of re-queuing the same bad note indefinitely
- use the exact canonical artifact filenames required by completion, not
  semantically similar alternates
- requeue only into a role whose inbox and inflight lanes are currently empty
- avoid creating late-phase acceptance or integration-review work before the
  earlier phase-0 through phase-4 canonical artifact set is complete
- prefer recovery notes in the owning role inbox over silent automatic edits

Blocked recovery notes emitted by `orchestrator` or `ceo` MAY reference
task-bundle prerequisites that are themselves the declared missing recovery
targets. The handoff validator MUST allow that exact pattern, because the
recovery note exists to restore those prerequisites.

Recovery queue synthesis is a required orchestrator responsibility. When
completion still fails and no inflight work can legally advance the run, the
orchestrator MUST turn canonical blockers into owner-specific recovery notes
instead of waiting passively for the queue to refill.

The recovery pass MUST also reopen Phase 5 implementation when the artifact
packages are ready but required generated-app outputs under `app/` have not
been materialized yet.

Those recovery notes MUST:

- identify the exact canonical files to create or repair
- use canonical filenames, not semantically similar alternates
- request downstream handoffs when the repaired artifact should reopen the next
  gate

Generic `orchestrator` recovery notes MUST NOT be treated as normal blocked
Architect integration or drift work when deciding whether to skip Product
Manager dispatch or when reporting blocked integration lanes.

## Handoff validation

Before dispatching a claimed inbox item, the orchestrator MUST validate the
handoff inputs.

At minimum that validation MUST check:

- every referenced required read exists unless the message explicitly marks it
  as the missing output to be created by the receiver
- referenced run-owned prerequisite artifacts are not still `status: stub`
- task-bundle prerequisite artifacts exist and are not still `status: stub`
- a handoff with `gate status: pass` or `pass with assumptions` does not
  advance past missing canonical prerequisites

If the handoff is invalid, the orchestrator MUST:

- reject the receiver dispatch
- create a correction note back to the sender when the sender is a normal role
- record the rejection in `runs/current/remarks.md` and
  `runs/current/evidence/orchestrator/recovery-log.md`

## Stall detection

The orchestrator MUST detect a stalled run.

A run is stalled when all of the following are true:

- the completion checker still fails
- no actionable inbox or inflight items remain under
  `runs/current/role-state/*/`
- no role turn completed useful work in the current control cycle

When a stall is detected, the orchestrator MUST:

- append a human-readable diagnosis to `runs/current/remarks.md`
- create a CEO inbox note describing the stall
- invoke the CEO role once before deciding the run is irrecoverable
- terminate non-zero only if the CEO intervention does not restore forward
  progress

The CEO intervention path MUST:

- start by checking whether the run is actually blocked or merely slow
- load broad context only because the orchestrator explicitly declared a stall
- either restore forward progress directly or emit the handoffs needed to
  restore progress
- avoid becoming a normal always-on review role

## Active-but-idle detection

The orchestrator MUST detect "alive but not progressing" states, not only
fully empty-queue stalls.

If actionable inbox or inflight work still exists, but no recent
`agent-start`, `agent-finish`, or worker heartbeat has occurred within the
configured idle threshold, the orchestrator MUST:

- append a diagnosis to `runs/current/remarks.md`
- emit a visible operator log line
- terminate non-zero instead of sleeping indefinitely

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
- that the claimed inflight item must be moved to `processed/`
- that the final response must begin with `Summary:`

The orchestrator SHOULD NOT inline large blocks of playbook text on every
turn.
