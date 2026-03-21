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

For any task that resolves `rule-mapping.md`, edits `app/rules/**`, proposes
custom Python rule behavior, or verifies LogicBank event/API behavior, the
agent MUST also load `../../../skills/logicbank-rules-design/SKILL.md`.

The agent MUST load these files first:

For the starter domain:

- [lifecycle.md](lifecycle.md)
- [domain-contract.md](domain-contract.md)
- [patterns.md](patterns.md)

For a non-starter domain:

- [../../../runs/current/artifacts/backend-design/model-design.md](../../../runs/current/artifacts/backend-design/model-design.md)
- [../../../runs/current/artifacts/backend-design/rule-mapping.md](../../../runs/current/artifacts/backend-design/rule-mapping.md)
- [../../../runs/current/artifacts/product/business-rules.md](../../../runs/current/artifacts/product/business-rules.md)

Then use the starter rule docs as examples rather than as domain truth.

The agent MUST also consult:

- `../../../runs/current/artifacts/architecture/capability-profile.md`
- `../../../runs/current/artifacts/architecture/load-plan.md`

The agent MAY load these files on demand:

- [boundaries-and-errors.md](boundaries-and-errors.md)
  when defining write paths, rollback behavior, API error mapping, or custom
  Python endpoints
- [validation.md](validation.md)
  when writing tests or checking rule behavior across create/update/delete flows
- [logicbank-reference.md](logicbank-reference.md)
  only when the current task is implementing `app/rules/rules.py`,
  resolving `backend-design/rule-mapping.md`, verifying actual LogicBank API
  behavior, or adding advanced event-driven rule logic

The skill above is the default day-to-day rule-selection guide. This contract
directory and the advanced LogicBank reference still own normative
enforcement, lifecycle, and verification expectations.

The agent MUST NOT load `logicbank-reference.md` for unrelated backend work.
That file exists to keep advanced LogicBank knowledge confined and out of the
default backend context budget.

The spec in this directory is the contract. The agent MUST NOT treat any
repo-local rule file as the source of truth unless the required pattern is
also shipped under `../../../templates/`.

Human-readable business-rule intent is owned by:

- `../../../runs/current/artifacts/product/business-rules.md`

The rules contract in this directory defines executable enforcement only. It
MUST NOT become a second competing human-readable source of business meaning.

Optional feature packs live under `../../features/` and MUST be loaded only
when enabled by the run capability profile and assigned to backend/rules work
in the load plan.
