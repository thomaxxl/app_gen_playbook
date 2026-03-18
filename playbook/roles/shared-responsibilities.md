# Shared Responsibilities

These rules apply to every agent.

Load `../summaries/global-core.md` first. This file expands only the shared
details that need more precision than the global summary.

## General

- Stay within the scope owned by the current role.
- Do not silently fill cross-layer gaps that belong to another role.
- Do not treat assumptions as confirmed facts.
- Record any assumption made because the input or upstream artifacts were
  incomplete.
- Load only the core contracts, templates, and feature packs authorized for
  the current role by `runs/current/artifacts/architecture/load-plan.md`.
- Disabled or undecided optional feature packs MUST NOT be loaded, summarized,
  copied into local gitignored `app/`, or used as design input.
- Business-rule intent is owned by Product through
  `runs/current/artifacts/product/business-rules.md`.
- Authoritative rule execution is owned by Backend.
- User-visible dynamic or ephemeral data is owned by the backend/API contract,
  not by frontend JavaScript literals.
- Frontend MAY mirror only the subset of approved rules explicitly marked for
  mirroring.
- Mirrored frontend validation exists for UX and latency only; it MUST NOT
  replace backend enforcement.
- DevOps owns package-management policy, runtime or toolchain packaging, and
  deployment packaging. DevOps MUST NOT silently change application semantics,
  API behavior, UX behavior, or business-rule enforcement.
- The authoritative run policy for dependency creation versus reuse lives in
  `runs/current/artifacts/architecture/dependency-provisioning.md`.
- CEO is a dormant exception role. It MUST run only for orchestrator-declared
  stall intervention or an explicit operator request.
- During normal execution, CEO MUST NOT be treated as an additional default
  participant in the phase pipeline.

When `dependency_provisioning.mode = preprovisioned-reuse-only`:

- no role may create a new virtualenv
- no role may run `pip install`, `pip wheel`, `npm install`, `npm ci`,
  `pnpm install`, `yarn install`, `playwright install`, or equivalent
  dependency-mutating commands
- no role may auto-install tools through implicit package-manager behavior
- roles may only verify, reuse, and normalize the approved dependency roots
- missing dependencies are an operator or environment block, not a role-owned
  repair task

When a run-owned or implementation surface needs dynamic, time-varying,
database-backed, workflow-backed, or environment-backed data:

- Architecture MUST classify the source in
  `runs/current/artifacts/architecture/data-sourcing-contract.md`
- Backend MUST expose the approved API/resource/read-model/meta contract
- Frontend MUST fetch that data instead of embedding it in the bundle
- if the contract is missing or the backend does not expose the needed data,
  roles MUST escalate the gap instead of hardcoding substitute values

## Artifact discipline

- Update the files owned by the current role.
- If a role-owned artifact is missing, create it instead of hiding decisions in
  inbox messages or agent narrative.
- Keep handoff decisions visible in the persistent artifact files, not only in
  `context.md`.
- Only the owning role may directly edit an artifact area unless ownership is
  explicitly delegated through a handoff.

Canonical ownership and writable-boundary rules live in:

- `../process/ownership-and-edits.md`
- `../routing/role-core.yaml`

Exception rule:

- during an orchestrator-declared stall, CEO MAY temporarily assume any
  run-owned artifact or local `app/` responsibility required to restore
  progress
- CEO MUST return control to the normal owner as soon as the stall is cleared
- CEO MUST NOT use this exception to edit playbook source unless the task
  explicitly became playbook maintenance

## Artifact metadata

Persistent artifact files in `runs/current/artifacts/product/`,
`runs/current/artifacts/architecture/`, `runs/current/artifacts/ux/`, and
`runs/current/artifacts/backend-design/`, and
`runs/current/artifacts/devops/` must start with a small metadata block
matching:

- `../../specs/contracts/artifact-frontmatter-template.md`

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
- Process at most one inbox item per noninteractive Codex invocation.
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
