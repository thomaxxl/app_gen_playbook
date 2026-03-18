# Backend Spec

This directory is the detailed backend contract for the playbook-generated app
style.

This directory is part of the playbook and defines the implementation
contract. Generated application source files must be written under `app/`, not
here.

Normative language in this directory MUST be interpreted using RFC 2119-style
semantics:

- `MUST` / `MUST NOT`: absolute implementation requirements
- `SHOULD` / `SHOULD NOT`: strong defaults that MAY be changed only with an
  explicit documented reason
- `MAY`: permitted optional behavior

The agent MUST NOT load every file by default. It MUST load only the parts
needed for the current task.

The agent MUST load these files first:

- [dependencies.md](dependencies.md)
- [models-and-naming.md](models-and-naming.md)
- [runtime-and-startup.md](runtime-and-startup.md)
- [route-discovery.md](route-discovery.md)
- [data-sourcing.md](data-sourcing.md)

The agent MUST also consult:

- `../../../runs/current/artifacts/architecture/capability-profile.md`
- `../../../runs/current/artifacts/architecture/load-plan.md`

The agent MAY load these files on demand:

- [bootstrap-and-db-lifecycle.md](bootstrap-and-db-lifecycle.md)
  when defining seeding, empty-db behavior, or SQLite lifecycle
- [api-contract.md](api-contract.md)
  when implementing SAFRS payloads or aligning frontend/backend assumptions
- [query-contract.md](query-contract.md)
  when implementing filtering, search, pagination, sort, or include behavior
- [sessions-and-transactions.md](sessions-and-transactions.md)
  when implementing request cleanup, commits, rollbacks, or custom endpoints
- [validation.md](validation.md)
  when writing tests or checking the generated backend contract
- [verification-fallbacks.md](verification-fallbacks.md)
  when the preferred local HTTP/ASGI verification path is broken
- [../../features/uploads/README.md](../../features/uploads/README.md)
  only when uploads are enabled for the run and backend work is in scope

Optional feature packs live under `../../features/` and MUST be loaded only
when enabled by the run capability profile. Disabled or undecided feature
packs MUST NOT be used as design input.

The spec in this directory is the contract. The agent MUST NOT treat any
repo-local app as the source of truth unless the required files are also
shipped under `../../../templates/`.

The backend MUST enforce every approved rule ID listed in:

- `../../../runs/current/artifacts/product/business-rules.md`

even when the same rule is mirrored in the frontend.
