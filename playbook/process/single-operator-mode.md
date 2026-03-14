# Single-Operator Mode

This file defines how one person or one orchestrating agent may execute the
playbook sequentially without collapsing the role model.

## Rule

A single operator may act in multiple roles serially, but must preserve the
same artifact and inbox discipline as a multi-agent run.

## Required behavior

- do not skip owned artifacts
- do not skip inbox handoffs just because the same operator holds the next role
- create the same handoff markdown files that a multi-agent run would create
- move processed handoffs into `processed/` as usual
- maintain separate `context.md` files per role directory
- preserve filename timestamps and ordering
- record any deviation taken only because the run was single-operator

## Historical-preserving app-only path

A single operator MAY preserve `../../runs/current/` and modify only
local `../../app/` when all of the following are true:

- the task is explicitly scoped to an already-generated app
- the operator is not claiming to perform a new full run
- the operator records that `../../runs/current/` was intentionally preserved
  and is not the authoritative run record for the current app state

This exception MUST NOT be used to avoid required handoffs during a real new
run. It exists only for app-only maintenance or evaluation passes.

## What this prevents

Single-operator mode must not turn into:

- undocumented direct edits across role boundaries
- silent phase compression
- “mental handoffs” with no inbox record
- skipping artifact gates

## Acceptance rule

A single-operator run is valid only if the resulting artifacts and inbox traces
still show the same phase and handoff structure that a multi-agent run would
have produced.
