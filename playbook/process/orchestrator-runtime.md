# Orchestrator Runtime

This file defines the expected runtime behavior of `scripts/run_playbook.sh`.

## Purpose

The orchestrator MUST:

- support `new-full-run`, `iterative-change-run`, `app-only-hotfix`, and
  `--resume`
- support an optional top-level `--yolo` operator flag that can affect the
  full run
- create a fresh local `runs/current/` from `runs/template/` for a new full
  run
- seed the Product Manager inbox from the supplied brief or change request
- process exactly one inbox message per Codex role invocation
- keep durable run state in artifacts, inbox traces, and role-local
  `context.md`
- use Codex session resume only as a speed and continuity layer
- log visible start and finish lines for every agent turn
- stop and surface a clear reason when the run becomes non-progressing
- treat missing or placeholder quality evidence as a gate blocker, not as an
  optional review detail
- keep the CEO role dormant unless a stall candidate is detected or the
  operator explicitly targets the CEO role
- validate handoff inputs before dispatching the receiver
- surface canonical output filenames to the active role at prompt time when
  the current phase or task bundle implies them
- refuse to declare completion while required run-owned artifacts remain
  missing, stub, or blocked, or while required generated-app outputs under
  `app/` are still absent
- stop early with an operator-action block when the active run requires
  pre-provisioned dependency reuse but the declared dependency roots are
  missing or incomplete
- stop before dispatching or resuming role work when the current app-backed
  run fails execution-environment preflight for dependencies, preview
  entrypoint availability, port binding, or Playwright capture

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

Transient Codex stream reconnect events recorded as JSONL `error` items MUST
NOT be treated as fatal if the same turn later reaches `turn.completed` and
produces a non-empty final result message. The orchestrator MUST only fail the
turn for transport-layer `error` events when no later successful completion is
present, or when Codex emits `turn.failed`.

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

If the operator starts `scripts/run_playbook.sh` with `--yolo`, the
orchestrator MUST translate that operator flag into
`--dangerously-bypass-approvals-and-sandbox` for every role turn in that run.
It MUST NOT combine yolo mode with `--full-auto`.

The orchestrator SHOULD also honor:

- `PLAYBOOK_RUNTIME_ENV=sandbox|host`

It MUST record that setting in `runs/current/orchestrator/runtime-environment.json`.

If the operator does not set `PLAYBOOK_RUNTIME_ENV`, the orchestrator SHOULD
default to `host`. `sandbox` remains an explicit opt-out for environments
where host-side bind, app startup, or browser capture is intentionally
unavailable.

When `PLAYBOOK_RUNTIME_ENV=host`, the orchestrator MUST write a host-runtime
preflight artifact under:

- `runs/current/evidence/host-runtime-verification.md`

That artifact SHOULD at minimum capture:

- whether localhost bind succeeds for the declared frontend and backend ports
- whether the approved backend runtime path can import the required FastAPI
  stack

The playbook SHOULD also maintain a DevOps-owned execution-environment
prerequisite artifact under:

- `runs/current/artifacts/devops/execution-prereqs.md`

That prerequisite check SHOULD be produced by
`tools/check_execution_prereqs.py` from inside the current execution context
and SHOULD cover:

- backend venv availability
- frontend `node_modules` availability
- localhost port bind capability
- Playwright screenshot capture capability
- Docker availability as an optional check

Before entering the main control loop for a run that already has
`app/frontend/package.json`, the orchestrator MUST run that execution
prerequisite check and stop immediately with `operator-action-required.md` if
any required check fails. Recording a blocked prerequisite artifact is not
enough; the run MUST NOT proceed into role dispatch until the current
execution context validates.

For browser-level launcher proof, the playbook SHOULD maintain:

- `runs/current/evidence/frontend-browser-proof.md`

The repository SHOULD provide a host-capable capture helper such as:

- `tools/capture_frontend_browser_proof.py`

When the generated app exposes `npm run capture:ui-previews`, that helper
SHOULD treat the app-provided capture script as the canonical screenshot
path. It SHOULD only fall back to generic direct-route capture when the app
does not provide a preview-capture script.

That helper SHOULD populate:

- `runs/current/evidence/frontend-browser-proof.md`
- `runs/current/evidence/ui-previews/manifest.md`
- `runs/current/evidence/ui-previews/*.png`

If `runs/current/artifacts/devops/execution-prereqs.md` proves
`playwright_screenshot: ok` and the generated app exposes
`capture:ui-previews`, the orchestrator MUST NOT accept a synthetic
`environment-blocked` preview manifest without attempting that app-provided
capture path first.

If host-runtime preflight proves the previously cited bind and backend-runtime
constraints are satisfied, the orchestrator MUST treat any older
`operator-action-required.md` file based only on those constraints as stale,
archive it, and continue routing work instead of blocking immediately.

Before the orchestrator exits non-successfully for a runner-owned blocked,
stall, or active-but-idle condition, it MUST give CEO a chance to review that
termination unless the terminating artifact was already produced by CEO.
CEO approval of termination is expressed by either:

- restoring progress so the run continues
- writing `runs/current/orchestrator/operator-action-required.md`
- writing `runs/current/orchestrator/pause-requested.md`

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

If an optional queue directory such as `runs/current/role-state/orchestrator/inbox/`
is absent in an older or partially initialized run, the orchestrator MUST
treat that lane as empty. It MUST NOT call `find` or similar scanners on a
missing optional queue path and spam the console with repeated errors.

When an orchestrator exception note is received, the orchestrator SHOULD
archive it under `runs/current/role-state/orchestrator/processed/` and convert
it into an explicit CEO intervention note unless a more specific automatic
recovery path is defined.

Actionable-work accounting MUST be based on canonical direct queue lanes only.
The orchestrator MUST NOT recursively count any Markdown file under
`runs/current/role-state/**/inbox/` or `**/inflight/` as live work, because
nested copied paths or other noncanonical debris can otherwise trigger false
active-but-idle failures.

Before completion or liveness enforcement, the orchestrator SHOULD normalize
queue layout by:

- migrating direct top-level legacy `runs/current/role-state/deployment/`
  inbox and inflight work into `runs/current/role-state/devops/` when the
  canonical `devops/` lane exists
- quarantining noncanonical nested queue traces under orchestrator evidence so
  they no longer count as live work

Before claiming work for any runtime role, the orchestrator MUST quarantine
duplicate queue traces. If a message basename already exists in `processed/`,
an `inflight/` or `inbox/` copy of that same basename MUST be archived as a
duplicate trace instead of being re-run. The orchestrator MUST preserve the
duplicate file as evidence and MUST NOT misclassify that condition as a role
implementation failure.

Before Phase 6, the orchestrator SHOULD refuse to treat integration review as
passing if the required implementation evidence inputs are missing or still
placeholder.

Before Phase 7, the orchestrator MUST refuse to dispatch or accept Product
Manager acceptance work unless the full integration-review evidence pack
exists, is no longer placeholder, and integration is not blocked.

Missing or placeholder quality evidence MUST be treated the same way as any
other required gate blocker.

When
`runs/current/artifacts/architecture/dependency-provisioning.md` declares
`mode: preprovisioned-reuse-only`, the orchestrator MUST run a dependency
preflight before dispatching DevOps, Frontend, or Backend work. If the
declared prepared dependency roots are missing or incomplete, the orchestrator
MUST write `runs/current/orchestrator/operator-action-required.md` and stop
instead of invoking installer behavior indirectly through the roles.

If a newer pending `from: operator` inbox or inflight note exists after an
earlier `runs/current/orchestrator/operator-action-required.md` was written,
the orchestrator MUST archive that stale operator-action file and let the
newer operator note run before reissuing the same blocked diagnosis.

If the current run is in `PLAYBOOK_RUNTIME_ENV=host` and
`runs/current/evidence/host-runtime-verification.md` proves that localhost bind
and the approved backend runtime path are available, the orchestrator MUST NOT
preserve or recreate an operator-action block that still cites only the old
sandbox listener failure or default-interpreter dependency failure. It MUST
route the next verification or recovery step instead.

## Writable-root rule

When the orchestrator starts Codex from a role-local runtime directory under
`runs/current/role-state/<role>/`, it MUST also grant writable access to the
role's owned sibling artifact and `app/` lanes.

At minimum, the orchestrator MUST grant:

- the role-local runtime directory
- the role-owned artifact directory under `runs/current/artifacts/`
- the role-owned `app/` subtree or root-owned app files
- the shared `runs/current/role-state/` tree for inbox handoffs

For CEO stall intervention, when the blocker is inside the local playbook
runtime itself, the orchestrator MUST also grant writable access to:

- `playbook/`
- `scripts/`
- `tools/`

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

Any actionable file already present in `runs/current/role-state/ceo/inbox/`
MUST be treated as a high-priority control note. After exception-lane routing,
the orchestrator MUST run CEO before recovery synthesis, Product Manager,
Architect, Deployment, or Phase-5 background-worker checks.

That rule allows an operator to steer a live run by writing a normal inbox
message directly into the CEO lane without modifying the runner process itself.

If CEO writes `runs/current/orchestrator/pause-requested.md`, the orchestrator
MUST stop the run cleanly instead of continuing normal dispatch. A later
`scripts/run_playbook.sh --resume` MUST archive that pause file and continue
from the current run state.

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
- archive `runs/current/orchestrator/pause-requested.md` if it exists, because
  `--resume` is an explicit operator decision to continue
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
- reopen only the earliest unmet early-phase frontier:
  Product first, then Architect, then Phase 3 and Phase 4 in parallel
- avoid creating late-phase acceptance or integration-review work before the
  earlier phase-0 through phase-4 canonical artifact set is complete
- prefer recovery notes in the owning role inbox over silent automatic edits

When the orchestrator rejects a downstream handoff and writes a correction note
back to the sender, that correction note MUST point at the archived rejected
handoff under the receiver `processed/` lane, not the transient `inflight/`
path that existed before rejection.

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
- directly repair local playbook-runtime defects under `playbook/`,
  `scripts/`, or `tools/` when those defects are the blocker keeping the run
  stalled
- approve or reject any pending non-success playbook termination before the
  orchestrator exits
- write `runs/current/orchestrator/operator-action-required.md` when the
  remaining blocker requires external operator action, environment
  provisioning, credentials, or a policy decision the agents cannot make
  after local repair paths have been exhausted
- record every CEO unblock intervention in `runs/current/remarks.md`
- avoid becoming a normal always-on review role

When `runs/current/orchestrator/operator-action-required.md` exists, the
orchestrator MUST terminate non-zero with that file's contents as the final
operator-facing diagnosis instead of continuing to re-queue recovery work.

Exception: if a newer pending `from: operator` note exists, the orchestrator
MUST treat that note as a superseding unblock attempt, archive the stale
operator-action file, and give the operator note precedence over generic
recovery or CEO re-escalation.

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

## Recovery emission rule

The orchestrator MUST NOT synthesize recovery notes while actionable inbox or
inflight work still exists elsewhere in the run. Recovery synthesis is a
queue-drain fallback, not a replacement for still-runnable downstream work.

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
