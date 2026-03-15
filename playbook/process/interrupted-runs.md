# Interrupted Runs

Interrupted runs are a normal operating condition.

The playbook MUST support deterministic continuation after:

- orchestrator termination
- Ctrl+C
- machine restart
- lost Codex session
- half-completed role work

## Canonical recovery state

The authoritative recovery state is:

- owned artifacts
- `runs/current/role-state/<role>/context.md`
- `runs/current/role-state/<role>/inflight/`
- inbox and processed traces
- `runs/current/orchestrator/run-status.json`
- worker state under `runs/current/orchestrator/workers/`

Codex session continuity is only an acceleration layer.

## Recovery algorithm

When the orchestrator resumes:

1. read `runs/current/orchestrator/run-status.json`
2. inspect every role `inbox/`, `inflight/`, `processed/`, and `context.md`
3. reconcile stale or unfinished inflight work
4. validate ownership before continuing
5. repair half-completed transitions when artifacts show the work already
   finished
6. return to normal dispatch once inflight work is reconciled

## Atomic completion rule

A role turn is complete only when all of these are true:

1. owned artifacts are updated
2. `context.md` is updated
3. downstream handoffs are written if required
4. required evidence is written
5. the claimed work item leaves `inflight/` and is archived to `processed/`
6. worker state is updated

## Resume policy

Resume the same Codex session only when:

- a stored session id exists
- the claimed inflight item still exists
- the session can be resumed cleanly
- there is no ownership-violation evidence

Rebuild from repo state when:

- no session id exists
- session resume fails
- the run state is inconsistent
- the interrupted role left partial writes that need review
