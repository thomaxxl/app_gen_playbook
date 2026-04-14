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
- Blocked self-handoffs and CEO/orchestrator recovery notes MAY include a
  `## Required Scope` section with exact file paths or narrow globs needed for
  that one repair turn.
- When present, `Required Scope` temporarily extends only the addressed role's
  runtime writable roots for that turn in addition to role-core writable
  paths.
- `Required Scope` MUST stay narrowly targeted and MUST NOT bypass global
  forbidden-write zones such as `specs/**`, `templates/**`, or `examples/**`.
- Any process an agent starts for a turn is part of that turn's responsibility.
  Agents MUST terminate servers, watchers, previews, or helper processes they
  started before moving the claimed inflight item into `processed/`.
- Agents MUST NOT rely on parallel background work to finish later after they
  hand off. If persistent runtime work is required, it must be explicitly
  orchestrator-owned and recorded as such.
- Verification shell snippets MUST be executable as written and MUST use
  stdin/exit-status patterns that actually match the intended check.
- Agents MUST NOT combine a producer pipeline with `python - <<'PY'` or
  similar heredoc patterns that replace the consumer stdin and silently discard
  the piped payload.
- When validating JSON from a command, agents SHOULD either:
  - pipe into `python -c '...'`
  - write the payload to a temp file and parse that file
  - or use `jq`
- When a shell check depends on a pipeline, agents MUST use a form that
  preserves the real producer failure status instead of reading only the last
  command's success.

When `dependency_provisioning.mode = reuse-preferred` or the legacy alias
`preprovisioned-reuse-only`:

- roles SHOULD reuse the approved dependency roots first when they already
  exist
- roles MAY create or repair the backend virtualenv, frontend dependency tree,
  and Playwright browser runtime inside the approved roots
- roles MAY run `pip install`, `pip wheel`, `npm install`, `npm ci`,
  `pnpm install`, `yarn install`, `playwright install`, or equivalent
  dependency-mutating commands when that repair is needed to advance the run
- roles MUST keep those repairs inside the approved backend/frontend dependency
  roots and MUST NOT silently redesign package sources or versions

When a run-owned or implementation surface needs dynamic, time-varying,
database-backed, workflow-backed, or environment-backed data:

- Architecture MUST classify the source in
  `runs/current/artifacts/architecture/data-sourcing-contract.md`
- Backend MUST expose the approved API/resource/read-model/meta contract
- Frontend MUST fetch that data instead of embedding it in the bundle
- if the contract is missing or the backend does not expose the needed data,
  roles MUST escalate the gap instead of hardcoding substitute values

When a user-visible or operator-visible concept maps cleanly to a persisted
database-backed table or relationship:

- the default delivery lane is a SAFRS JSON:API resource or relationship
- the default implementation lane is a mapped SQLAlchemy ORM model and
  relationship, not ad hoc row-dict assembly or raw-SQL-only handlers
- before approving a custom endpoint for that DB-backed data, roles must
  document why ordinary SAFRS resource, relationship, `include=...`,
  `jsonapi_attr`, or `jsonapi_rpc` does not fit
- Architecture MUST treat that as the default unless the run-owned artifacts
  record an explicit exception and replacement contract
- Backend MUST NOT replace that default with a custom `/api/ops/` or ad hoc
  JSON endpoint merely because a custom summary page also exists
- Backend MUST NOT bypass the ORM as the primary implementation path for that
  resource unless the run-owned artifacts document why ORM mapping is not the
  right fit
- Frontend MUST treat custom read-model endpoints as supplements for
  dashboards, aggregates, or operational summaries, not as justification to
  bypass the underlying SAFRS resource/relationship lane
- approved exceptions are limited to internal-only concepts,
  singleton/settings-like concepts, pure aggregate/read-model payloads, and
  documented security/performance cases where direct resource exposure is not
  appropriate
- `JABase` is an explicit exception lane, not a silent shortcut

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
- during that same stall-only exception path, CEO MAY also repair local
  playbook-runtime defects under `playbook/`, `scripts/`, and `tools/` when
  those defects are the blocker preventing the current run from advancing
- CEO MUST return control to the normal owner as soon as the stall is cleared
- CEO MUST record ordinary unblock interventions in owned evidence/runtime
  files and MAY promote only durable playbook/process feedback into
  `runs/current/remarks.md`
- CEO MUST NOT use this exception to edit `specs/`, `templates/`, or unrelated
  playbook source beyond the local runtime repair needed to unblock the
  current run unless the task explicitly became playbook maintenance

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

Each runtime-created `context.md` MUST stay compact and durable.

It SHOULD keep only context that still matters for future turns or future runs,
for example:

- stable decisions still in force
- durable assumptions worth preserving
- unresolved issues that remain open across handoffs or recovery
- reusable pitfalls, upstream bugs, or gotchas that future runs should avoid
- pointers to the canonical artifact or evidence file when that pointer is
  still useful later

It MUST NOT become an append-only execution log. Move transient detail into the
real canonical surfaces instead, such as inbox history, processed handoffs,
`runs/current/notes.md`, verification artifacts, or role-owned evidence files.

Examples of material that SHOULD NOT remain in `context.md` once the turn is
complete:

- last processed inbox filenames
- exhaustive file-change lists
- shell command transcripts
- one-off tested routes or ad hoc verification snippets
- implementation evidence that already lives in a canonical artifact

Roles SHOULD compact `context.md` regularly by rewriting it in place, removing
resolved or stale detail instead of only appending new notes.

`runs/current/remarks.md` is reserved for curated playbook feedback only.
Normal runtime roles MUST NOT use it as a shared execution diary, approval log,
verification log, or stale-blocker scratchpad. They SHOULD record those details
in `runs/current/notes.md`, role-owned artifacts, or evidence files instead.
The orchestrator is the normal direct writer for `runs/current/remarks.md`.
All roles, including CEO, should surface durable playbook feedback through
their owned notes/artifacts and explicit handoffs; if that feedback matters,
the orchestrator can promote it into `remarks.md`.

When recording verification results in `context.md`, evidence artifacts, or
`runs/current/notes.md`, agents MUST state explicitly whether the check
confirmed a healthy state or exposed a defect. Do not use wording that makes
success metrics read like an unresolved blocker.

## Escalation

- If the role cannot proceed without inventing a product or architecture
  decision, it must hand the issue to the correct upstream agent.
- If implementation reveals a broken contract, send the correction request back
  to the owning agent and document it.
- Sparse input alone is not escalation. The Product Manager must first try to
  resolve it through research and explicit product framing.
