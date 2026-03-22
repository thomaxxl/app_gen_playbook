---
name: logicbank-request-pattern
description: Use when SQLAlchemy-backed business behavior needs a request/response or audit-style integration row, thin business wrapper, or nested rule-driven insert that should stay on the LogicBank transaction path instead of moving business logic into an endpoint or service layer.
---

# LogicBank Request Pattern

Use this skill when the requirement involves:

- a `Sys*`, request, audit, command, or response row
- an API call that must return rule-derived response fields from a created row
- nested creation of request/audit rows during rule execution
- a thin wrapper around LogicBank-managed write behavior

## Core stance

Request Pattern is an optional advanced lane.

It is appropriate when:

- the request itself is meaningful persisted data
- the caller needs response-bearing fields populated by rule execution
- the system needs an auditable request/response record

It is not appropriate when:

- a normal SAFRS resource write already expresses the behavior cleanly
- the endpoint is becoming a fat service that owns the business logic
- the wrapper only exists because the rule design was not mapped clearly

## Thin-wrapper rule

The HTTP layer may create or name the request, but it must remain thin.

The wrapper:

- may validate transport shape and auth
- may instantiate the request row
- may call the normal ORM / LogicBank commit path
- must not own the business invariant itself

The business behavior belongs in LogicBank rules and approved events.

## Event choice

Use:

- `early_row_event` when the request needs response fields computed in the same transactional path before the caller reads back the row
- `after_flush_row_event` for fire-and-forget integrations, emitted side effects, or cases that need flushed ids but do not feed the immediate response contract

Do not use `after_flush_row_event` just because it feels "later" if the caller needs the response values synchronously.

## Nested insert rule

When rule/event code must create a request or audit row, use:

```python
new_request_logic_row = logic_row.new_logic_row(RequestModel)
new_request_logic_row.insert(reason="...")
```

Do not use `session.add(...)` plus `flush()` inside the flush cycle as the primary nested-insert pattern.

## Observability

Advanced request/event code must use `logic_row.log(...)` for traceability.

Evidence should include:

- at least one logic trace snippet or equivalent grouped rule log
- one ORM-path test
- one API or wrapper-path test when the wrapper is part of the contract

## Required design records

Update:

- `runs/current/artifacts/backend-design/model-design.md`
- `runs/current/artifacts/backend-design/rule-mapping.md`
- `runs/current/artifacts/backend-design/test-plan.md`
- `runs/current/artifacts/backend-design/bootstrap-strategy.md` if new derived/request columns need backfill or seed support

Record:

- why ordinary CRUD was insufficient
- why the wrapper remains thin
- event choice (`early_row_event` vs `after_flush_row_event`)
- schema prerequisite / migration / backfill needs
- business entry-path tests and logic-trace evidence
