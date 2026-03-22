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
2. resolve the concrete `safrs-jsonapi-client` repo URL and checkout policy
3. materialize that source into `app/tmp/safrs-jsonapi-client`
4. keep `app/frontend/package.json` pointed at `file:../tmp/safrs-jsonapi-client`

The unresolved template token MUST remain in the template lane only.

The current maintained default for that source is:

- repo: `https://github.com/thomaxxl/safrs-jsonapi-client`
- checkout policy: latest upstream default-branch checkout
- local materialization path: `app/tmp/safrs-jsonapi-client`

unless the run-owned `runtime-bom.md` explicitly records and approves a
replacement.

It MUST NOT survive into:

- `app/frontend/package.json`
- generated install instructions
- generated lockfiles

The generated app MUST NOT expect npm to fetch `safrs-jsonapi-client`
directly from GitHub during normal clean install. The supported flow is to
clone or refresh the approved local checkout first, then install from that local file
dependency.

## Verification rule

Before delivery:

- no generated app file may contain `<REPLACE_WITH_...>` placeholder tokens
- if such a token remains, the run is incomplete
