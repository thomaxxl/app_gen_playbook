---
name: logicbank-allocation
description: Use when a SQLAlchemy-backed requirement involves allocation, distribution, apportionment, or split logic across provider, recipient, and allocation rows so the schema and rule design use the LogicBank allocation pattern instead of custom endpoint or service loops.
---

# LogicBank Allocation

Use this skill when the prompt or approved rules say:

- allocate
- distribute
- apportion
- split
- spread across recipients

## Core stance

Allocation is a distinct advanced pattern with schema consequences.

Do not treat it as "just another event."

The design usually needs:

- a provider row
- a recipient row
- an allocation/junction row
- explicit amount / remainder fields

Add those tables and relationships during schema design, not after endpoint code is already written.

## Preferred lane

If the requirement is a real allocation workflow, prefer the LogicBank
allocation extension and the provider/recipient/allocation model over custom
Python loops in endpoints or services.

## Schema-first rule

Record in `model-design.md` and `rule-mapping.md`:

- provider model
- recipient model
- allocation/junction model
- remaining/unallocated fields
- derived totals or counts affected by allocation
- migration/backfill implications for newly introduced fields

## Execution rule

Allocation code that creates allocation rows during rule execution must stay
on the LogicBank path and use `logic_row.new_logic_row(ModelClass)` plus
`.insert(...)` rather than ad hoc `session.add(...)/flush()` loops.

## Observability and tests

Allocation implementations must provide:

- one logic trace snippet using `logic_row.log(...)`
- one provider-to-recipients allocation test
- one exhaustion / no-remaining-balance test
- one re-run / duplicate-protection or idempotency note if relevant

## Boundary

Allocation is optional. Do not load this skill unless the run-owned prompt,
rule mapping, or architecture artifacts clearly call for allocation semantics.
