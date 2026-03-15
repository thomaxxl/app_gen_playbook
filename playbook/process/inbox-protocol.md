# Inbox Protocol

This file defines the actionable message model for agent handoffs.

## Inbox semantics

- Every agent directory contains an `inbox/`.
- Every agent directory also contains a `processed/` archive.
- Every agent directory SHOULD also contain an `inflight/` directory.
- Every markdown file in that inbox is actionable work.
- Inbox files are the active queue.
- Inflight files are claimed work currently being processed.
- Processed items are moved into `processed/` for traceability.
- Each noninteractive Codex role invocation MUST process at most one inbox
  item.

The permanent record belongs in:

- role-owned artifact files
- the agent's runtime-created `context.md`

## Filename convention

Inbox files must use this format:

- `YYYYMMDD-HHMMSS-from-<sender>-to-<receiver>-<topic>.md`

Example:

- `20260312-101500-from-product_manager-to-architect-product-handoff.md`

`INPUT.md` is the only intentional exception.

## Ordering rules

- Agents process inbox items oldest-first by filename timestamp.
- If a newer message supersedes an older one, the newer message must include:
  - `supersedes: <filename>`
- Blocked items remain in `inbox/` only if they are still actionable.
- If a blocked item is no longer actionable, move it to `processed/` and emit a
  follow-up handoff to the next responsible agent.

## Special file

- `runs/current/role-state/product_manager/inbox/INPUT.md`
  The initial user brief.

## Standard message shape

Any non-`INPUT.md` inbox message should include:

- `from`
- `to`
- `topic`
- `purpose`
- `required reads`
- `requested outputs`
- `dependencies`
- `gate status`
- `implementation evidence`
- `change_id` (optional)
- `change_type` (optional)
- `affected_artifacts` (optional)
- `affected_app_paths` (optional)
- `compatibility_impact` (optional)
- `migration_required` (optional)
- `regression_scope` (optional)
- `task_id` (optional)
- `supersedes` (optional)
- `blocking issues`
- `notes`

Standard orchestrator-created message topics:

- `recovery`
- `handoff-correction`
- `stall-intervention`

## Gate status values

Use one of:

- `pass`
- `pass with assumptions`
- `blocked`

## Sender responsibilities

The sending agent must:

1. update the permanent artifacts it owns
2. create the inbox message for the next agent
3. describe what changed, what assumptions were made, and what remains open
4. ensure the referenced artifacts are marked `ready-for-handoff` or
   `approved` before sending a handoff with `gate status: pass` or
   `pass with assumptions`
5. do not rely on `status: stub` artifacts as if they were authored inputs

## Receiver responsibilities

The receiving agent must:

1. read `role.md`
2. read its `context.md` if present
3. claim the oldest actionable inbox message into `inflight/` for the current turn
4. update owned artifacts
5. update `context.md`
6. send onward messages if needed
7. move the completed inflight message into `processed/`

## Atomic completion rule

From the playbook perspective, a role is not finished with a message until:

1. owned artifacts are updated
2. `context.md` is updated
3. downstream handoffs are written if needed
4. required evidence is written
5. the claimed item leaves `inflight/` and appears in `processed/`

## Gate signal

A handoff file with:

- `gate status: pass`
- or `gate status: pass with assumptions`

is the formal signal that the next phase may start.

That signal is valid only when the canonical prerequisite artifacts required by
the receiver actually exist and are not still `status: stub`.

## Completion rule

The app effort is complete only when:

- the product acceptance gate passes
- every required artifact exists
- no required artifact remains `status: stub`
- all core-agent inboxes are empty
- the dormant CEO lane is empty unless a stalled-run intervention is still
  actively being resolved
