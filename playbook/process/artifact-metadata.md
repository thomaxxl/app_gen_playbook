# Artifact Metadata

Use this file when creating or reviewing persistent artifacts in:

- `runs/current/artifacts/product/`
- `runs/current/artifacts/architecture/`
- `runs/current/artifacts/ux/`
- `runs/current/artifacts/backend-design/`
- local `app/docs/` after promotion, when used

Required metadata header format:

```md
owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - none
unresolved:
  - none
last_updated_by: product_manager
```

This is an unfenced YAML-like header block at the top of the file.

Allowed `status` values:

- `stub`
- `draft`
- `in-progress`
- `ready-for-handoff`
- `approved`
- `blocked`
- `interrupted`
- `needs-recovery`
- `superseded`

Rules:

- the metadata block belongs at the top of the file
- do not wrap it in front-matter delimiters
- do not wrap it in a fenced code block
- keep one blank line between the metadata header and the document title
- `depends_on` should name concrete files when there are real prerequisites
- `unresolved` should be explicit; use `none` only when nothing material is
  open
- `stub` means seeded placeholder content and must not be treated as a real
  authored artifact
- the owning role may set `draft` and `ready-for-handoff`
- `approved` must be set by the receiving or gate-owning review role, not by
  the current owner self-approving its own artifact
- that review role MAY edit only the metadata block when setting `approved`,
  `blocked`, `superseded`, `unresolved`, or `last_updated_by`
- the review role MUST NOT change artifact body content as part of approval
- an artifact MUST NOT be marked `approved` unless the gate-owning role has a
  corresponding processed inbox item and records the approval in its
  `context.md`
- if an approved artifact claims backend tests, frontend tests, or Playwright
  success, the artifact SHOULD reference supporting files under `evidence/`
- a handoff with `gate status: pass` or `pass with assumptions` should only
  reference artifacts marked `ready-for-handoff` or `approved`

Optional iteration metadata fields:

- `change_id`
- `baseline_ref`
- `compatibility`
- `supersedes`
- `implemented_in`
- `verification_refs`

## Approval example

Example lifecycle:

1. the owner writes the artifact and sets `status: draft`
2. the owner completes the first pass and sets `status: ready-for-handoff`
3. the receiving or gate-owning role reviews the artifact
4. if the body is acceptable, that review role MAY update only the metadata
   block to `status: approved`
5. if the body is not acceptable, that review role MAY update only the
   metadata block to `status: blocked` and record the unresolved review points
6. any body-content fix after a blocked review returns to the owning role
