owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: stub
depends_on:
  - ../product/business-rules.md
  - model-design.md
unresolved:
  - replace with run-specific rule mapping
last_updated_by: playbook

# Rule Mapping Template

This file is a generic template. The Backend role MUST create the run-owned
version at `../../runs/current/artifacts/backend-design/rule-mapping.md`.

## Required rule table

The real artifact MUST include a table with this shape:

| Product rule | Backend fields involved | LogicBank pattern | Trigger story | Persistence impact | Error behavior | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `<plain-language rule>` | `<fields>` | `<formula/sum/count/copy/constraint/custom>` | `<create/update/delete/reparent/etc.>` | `<stored derived field / validation only / both>` | `<rollback message or no error>` | `<notes>` |

The Backend role MUST replace the placeholder row.

## Required notes

The real artifact MUST also define:

- which product rules are declarative LogicBank rules
- which rules require custom Python behavior
- which fields are backend-managed because of those rules
- which rule requests are explicitly deferred or out of scope
