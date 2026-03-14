owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - brief.md
  - workflows.md
  - domain-glossary.md
unresolved:
  - none
last_updated_by: product_manager

# Business Rules

## Purpose

This file is the authoritative human-readable business-rules catalog for the
Airport Ops Control run.

## Domain Vocabulary Used In Rules

- Gate
- Flight
- FlightStatus
- active flight
- attention-required flight
- departed flight

## Defaults Not Listed Individually

- Default CRUD behavior comes from the generated admin stack.
- Default required-field and type validation is supplemented by the app-
  specific rules below.

## Rule Index

| Rule ID | Title | Class | Frontend Mirror | Status |
| --- | --- | --- | --- | --- |
| BR-001 | Gate scheduled flight rollup | derived-rollup | none | active |
| BR-002 | Gate active flight rollup | derived-rollup | none | active |
| BR-003 | Gate delay rollup | derived-rollup | none | active |
| BR-004 | Flight status field copy | copy-rule | none | active |
| BR-005 | Flight references are required | validation | form | active |
| BR-006 | Delay minutes are non-negative | validation | input | active |
| BR-007 | Attention flights require delay reason | validation | form | active |
| BR-008 | Departed flights require actual departure time | validation | form | active |

## Rule Entries

### BR-001

- Rule ID: BR-001
- Title: Gate scheduled flight rollup
- Status: active
- Rule Class: derived-rollup
- Plain-Language Rule: A `Gate.scheduled_flights` value must equal the count of
  related `Flight` records.
- Rationale: gate workload should never rely on manual totals.
- Source: product interpretation
- Trigger: create, update, delete of `Flight`
- Preconditions: none
- Valid Outcome: the stored rollup matches the related row count
- Invalid Outcome: manual or stale rollup value
- Example: Gate A1 has 3 flight rows, so `scheduled_flights = 3`
- Frontend Mirror: none

### BR-002

- Rule ID: BR-002
- Title: Gate active flight rollup
- Status: active
- Rule Class: derived-rollup
- Plain-Language Rule: A `Gate.active_flights` value must equal the sum of
  related `Flight.is_active` values.
- Rationale: active workload depends on status-driven behavior.
- Source: product interpretation
- Trigger: create, update, delete of `Flight`
- Preconditions: `is_active` is copied from `FlightStatus`
- Valid Outcome: gate active count reflects current active flights
- Invalid Outcome: active dashboard count does not match status-driven rows
- Example: two boarding flights and one departed flight yield `active_flights = 2`
- Frontend Mirror: none

### BR-003

- Rule ID: BR-003
- Title: Gate delay rollup
- Status: active
- Rule Class: derived-rollup
- Plain-Language Rule: A `Gate.total_delay_minutes` value must equal the sum
  of related `Flight.delay_minutes`.
- Rationale: supervisors need an aggregate delay indicator per gate.
- Source: product interpretation
- Trigger: create, update, delete of `Flight`
- Preconditions: `delay_minutes` is numeric and non-negative
- Valid Outcome: total delay is always recomputed from child rows
- Invalid Outcome: manual override or stale delay total
- Example: 15-minute and 30-minute delays yield `total_delay_minutes = 45`
- Frontend Mirror: none

### BR-004

- Rule ID: BR-004
- Title: Flight status field copy
- Status: active
- Rule Class: copy-rule
- Plain-Language Rule: A `Flight` record must copy `code`, `is_active`, and
  `requires_attention` from its related `FlightStatus`.
- Rationale: status-driven behavior must remain normalized and consistent.
- Source: product interpretation
- Trigger: create or update of `Flight` or parent `FlightStatus`
- Preconditions: `status_id` is present
- Valid Outcome: copied fields match the selected status definition
- Invalid Outcome: status-derived values drift from the parent reference
- Example: delayed status sets `flight_status_code = delayed` and
  `requires_attention = true`
- Frontend Mirror: none

### BR-005

- Rule ID: BR-005
- Title: Flight references are required
- Status: active
- Rule Class: validation
- Plain-Language Rule: A `Flight` record must include both `gate_id` and
  `status_id`.
- Rationale: flights are not meaningful without operational assignment.
- Source: product interpretation
- Trigger: create and update
- Preconditions: none
- Valid Outcome: save is allowed only when both references are present
- Invalid Outcome: null gate or status reference
- Example: a flight without a gate is rejected
- Frontend Mirror: form

### BR-006

- Rule ID: BR-006
- Title: Delay minutes are non-negative
- Status: active
- Rule Class: validation
- Plain-Language Rule: `Flight.delay_minutes` must be zero or greater.
- Rationale: negative delays have no business meaning in this app.
- Source: product interpretation
- Trigger: create and update
- Preconditions: none
- Valid Outcome: non-negative numeric value
- Invalid Outcome: negative delay minutes
- Example: `delay_minutes = -5` is rejected
- Frontend Mirror: input

### BR-007

- Rule ID: BR-007
- Title: Attention flights require delay reason
- Status: active
- Rule Class: validation
- Plain-Language Rule: A `Flight` with `requires_attention = true` must have a
  non-empty `delay_reason`.
- Rationale: disruptions need explicit context.
- Source: product interpretation
- Trigger: create and update
- Preconditions: `requires_attention` is copied from the selected status
- Valid Outcome: attention flights always carry an explanation
- Invalid Outcome: delayed records with blank reason
- Example: a delayed flight without `delay_reason` is rejected
- Frontend Mirror: form

### BR-008

- Rule ID: BR-008
- Title: Departed flights require actual departure time
- Status: active
- Rule Class: validation
- Plain-Language Rule: A `Flight` with `flight_status_code = departed` must
  include `actual_departure_at`.
- Rationale: completed departures need a recorded operational timestamp.
- Source: product interpretation
- Trigger: create and update
- Preconditions: status copy has run
- Valid Outcome: departed records always show an actual departure time
- Invalid Outcome: departed record saved without a timestamp
- Example: changing a flight to departed requires the actual departure value
- Frontend Mirror: form
- `Preconditions`
- `Applies To`
- `Valid Outcome`
- `Invalid Outcome`
- `User-Visible Consequence`
- `Backend Enforcement`
- `Frontend Mirror`
- `Frontend Mirror Reason`
- `Authoritative Error Message`
- `Examples`
- `Backend Test Required`
- `Frontend Test Required`

Optional but recommended:

- `Decision Table Ref`
- `Implementation Notes`
- `Traceability`
