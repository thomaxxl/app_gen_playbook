# Inbox Protocol

This file defines the actionable message model for agent handoffs.

## Inbox semantics

- Every agent directory contains an `inbox/`.
- Every agent directory also contains a `processed/` archive.
- Every markdown file in that inbox is actionable work.
- Inbox files are the active queue.
- Processed items are moved into `processed/` for traceability.

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
- `supersedes` (optional)
- `blocking issues`
- `notes`

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
3. process every inbox message
4. update owned artifacts
5. update `context.md`
6. send onward messages if needed
7. move the processed inbox messages into `processed/`

## Gate signal

A handoff file with:

- `gate status: pass`
- or `gate status: pass with assumptions`

is the formal signal that the next phase may start.

## Completion rule

The app effort is complete only when:

- the product acceptance gate passes
- every required artifact exists
- no required artifact remains `status: stub`
- all core-agent inboxes are empty
