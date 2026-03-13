# Rules Spec

This directory is the detailed LogicBank contract for the playbook-generated
app style.

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

For the starter domain:

- [lifecycle.md](lifecycle.md)
- [domain-contract.md](domain-contract.md)
- [patterns.md](patterns.md)

For a non-starter domain:

- [../../backend-design/model-design.md](../../backend-design/model-design.md)
- [../../backend-design/rule-mapping.md](../../backend-design/rule-mapping.md)
- [../../product/business-rules.md](../../product/business-rules.md)

Then use the starter rule docs as examples rather than as domain truth.

The agent MAY load these files on demand:

- [boundaries-and-errors.md](boundaries-and-errors.md)
  when defining write paths, rollback behavior, API error mapping, or custom
  Python endpoints
- [validation.md](validation.md)
  when writing tests or checking rule behavior across create/update/delete flows

The spec in this directory is the contract. The agent MUST NOT treat any
repo-local rule file as the source of truth unless the required pattern is
also shipped under `../../templates/`.
