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

Replace this stub with the run-specific rule mapping.

## Required rule table

| Product rule | Backend fields involved | LogicBank pattern | Trigger story | Persistence impact | Error behavior | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `<plain-language rule>` | `<fields>` | `<formula/sum/count/copy/constraint/custom>` | `<create/update/delete/reparent/etc.>` | `<stored derived field / validation only / both>` | `<rollback message or no error>` | `<notes>` |

## Required notes

- which product rules are declarative LogicBank rules
- which rules require custom Python behavior
- which rule requests are deferred or out of scope
