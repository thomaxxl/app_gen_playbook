# Shared Responsibilities

These rules apply to every agent.

## General

- Stay within the scope owned by the current role.
- Do not silently fill cross-layer gaps that belong to another role.
- Do not treat assumptions as confirmed facts.
- Record any assumption made because the input or upstream artifacts were
  incomplete.

## Artifact discipline

- Update the files owned by the current role.
- If a role-owned artifact is missing, create it instead of hiding decisions in
  inbox messages or agent narrative.
- Keep handoff decisions visible in the persistent artifact files, not only in
  `context.md`.
- Only the owning role may directly edit an artifact area unless ownership is
  explicitly delegated through a handoff.

Ownership map:

- `runs/current/artifacts/product/` -> Product Manager
- `runs/current/artifacts/architecture/` -> Architect
- `runs/current/artifacts/ux/` -> UX/UI + Frontend
- `runs/current/artifacts/backend-design/` -> Backend
- `specs/contracts/frontend/` -> UX/UI + Frontend technical contracts
- `specs/contracts/backend/` -> Backend technical contracts
- `specs/contracts/rules/` -> Backend technical contracts
- `specs/contracts/deployment/` -> optional Deployment role when packaging is in scope
- `specs/product/`, `specs/architecture/`, `specs/ux/`, and
  `specs/backend-design/` -> generic playbook template source

## Artifact metadata

Persistent artifact files in `runs/current/artifacts/product/`,
`runs/current/artifacts/architecture/`, `runs/current/artifacts/ux/`, and
`runs/current/artifacts/backend-design/` must start with a small metadata
block containing:

- `owner`
- `phase`
- `status`
- `depends_on`
- `unresolved`
- `last_updated_by`

Allowed `status` values:

- `stub`
- `draft`
- `ready-for-handoff`
- `approved`
- `blocked`
- `superseded`

## Inbox discipline

- Treat every `.md` file in `inbox/` as actionable input.
- Process inbox items oldest-first by filename timestamp.
- Move processed inbox files into `processed/` after the work is complete.
- If work is blocked, send a blocking note to the next responsible agent
  instead of leaving stale instructions in the inbox.
- If a newer inbox item replaces an older one, the newer file must explicitly
  declare `supersedes: <filename>`.

## Context discipline

Each runtime-created `context.md` should include:

- last processed inbox items
- files created or updated
- decisions made
- assumptions made
- unresolved issues
- handoffs emitted
- verification path used
- implementation evidence such as tested routes, commands, or generated files

## Escalation

- If the role cannot proceed without inventing a product or architecture
  decision, it must hand the issue to the correct upstream agent.
- If implementation reveals a broken contract, send the correction request back
  to the owning agent and document it.
- Sparse input alone is not escalation. The Product Manager must first try to
  resolve it through research and explicit product framing.
