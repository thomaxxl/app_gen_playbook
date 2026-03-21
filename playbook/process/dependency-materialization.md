# Dependency Materialization

This file defines how template placeholders become installable generated-app
dependency manifests.

## Core rule

Template files MAY contain unresolved source tokens when the maintained
playbook intends the actual artifact source to come from the run-owned
`runtime-bom.md`.

Generated app files under `app/` MUST NOT keep those unresolved tokens.

## Frontend rule

Before any frontend install step begins, the run MUST:

1. read `runs/current/artifacts/architecture/runtime-bom.md`
2. resolve the concrete `safrs-jsonapi-client` artifact source
3. write the concrete value into `app/frontend/package.json`

The unresolved template token MUST remain in the template lane only.

The current maintained default for that source is the GitHub release asset:

- `https://github.com/thomaxxl/safrs-jsonapi-client/releases/download/0.0.1/safrs-jsonapi-client-0.1.0.tgz`

unless the run-owned `runtime-bom.md` explicitly records and approves a
replacement.

It MUST NOT survive into:

- `app/frontend/package.json`
- generated install instructions
- generated lockfiles

## Verification rule

Before delivery:

- no generated app file may contain `<REPLACE_WITH_...>` placeholder tokens
- if such a token remains, the run is incomplete
