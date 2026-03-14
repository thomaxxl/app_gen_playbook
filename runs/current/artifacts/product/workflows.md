owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - brief.md
unresolved:
  - none
last_updated_by: product_manager

# Workflows

## WF-001 Create Gate

- User: gate coordinator
- Starting point: `Gate` create form
- Steps:
  1. Enter gate code, terminal, and zone.
  2. Save the gate.
  3. Review the list row and derived zero values.
- Success outcome: the new gate is available for flight assignment.
- Failure outcome: duplicate or invalid gate data is rejected.
- Touched resources: `Gate`
- Related stories: US-001
- Non-goals: no maintenance-block workflow in v1

## WF-002 Schedule Flight

- User: duty manager
- Starting point: `Flight` create form
- Steps:
  1. Enter flight number, destination, and scheduled departure time.
  2. Choose gate and status.
  3. Optionally enter delay metadata and actual departure time when relevant.
  4. Save the record.
- Success outcome: the flight appears in the board and gate rollups update.
- Failure outcome: missing references or invalid delay data block save.
- Touched resources: `Flight`, `Gate`, `FlightStatus`
- Related stories: US-001, US-002, US-004
- Non-goals: no passenger assignment

## WF-003 Escalate Delayed Flight

- User: operations supervisor
- Starting point: `Flight` edit form
- Steps:
  1. Change the status to an attention-required value.
  2. Enter delay minutes and delay reason.
  3. Save the record.
- Success outcome: the flight remains active and shows in delayed summaries.
- Failure outcome: blank delay reason or invalid delay minutes are rejected.
- Touched resources: `Flight`, `FlightStatus`, `Gate`
- Related stories: US-003, US-005
- Non-goals: no separate incident ticket

## WF-004 Close Departed Flight

- User: duty manager
- Starting point: `Flight` edit form
- Steps:
  1. Change status to `departed`.
  2. Enter `actual_departure_at`.
  3. Save the record.
- Success outcome: the flight no longer counts as active.
- Failure outcome: departed records without timestamp are rejected.
- Touched resources: `Flight`, `Gate`, `FlightStatus`
- Related stories: US-005
- Non-goals: no arrival follow-up workflow
