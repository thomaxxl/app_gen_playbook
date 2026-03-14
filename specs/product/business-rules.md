owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - brief.md
  - workflows.md
  - domain-glossary.md
unresolved:
  - replace with run-specific business rules
last_updated_by: playbook

# Business Rules Catalog Template

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/business-rules.md`.

This file is the single authoritative human-readable catalog of all
non-default business logic for the run.

The Product Manager MUST NOT create a second competing human-readable rule
source elsewhere in the run artifacts.

## Required top-level sections

The run-owned file MUST include these sections in this order:

1. `Purpose`
2. `Domain Vocabulary Used In Rules`
3. `Defaults Not Listed Individually`
4. `Rule Index`

## Rule-default boundary

The run-owned file MUST record every app-specific rule that goes beyond
baseline generated CRUD and generic library behavior.

The run-owned file MUST NOT be cluttered with ordinary platform defaults such
as:

- generated list/show/create/edit scaffolding
- generic type coercion with no domain significance
- generic library defaults that are not app-specific

If a behavior matters to the business flow or user experience, it MUST be
recorded here even when a library could implement it mechanically.

## Required rule index

The run-owned file MUST include a rule index table with this shape:

| Rule ID | Title | Class | Frontend Mirror | Status |
| --- | --- | --- | --- | --- |
| `BR-001` | `<title>` | `<class>` | `<mirror mode>` | `<status>` |

## Required rule entry schema

Every rule entry MUST include:

- `Rule ID`
- `Title`
- `Status`
- `Rule Class`
- `Plain-Language Rule`
- `Rationale`
- `Source`
- `Trigger`
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

The `Frontend Mirror` field MUST be one of:

- `none`
- `input`
- `form`
- `schema`
- `async`

`Backend Enforcement` MUST be `required` for every approved rule.

## Rule wording standard

The `Plain-Language Rule` MUST use controlled natural language. The Product
Manager SHOULD keep it short, explicit, and glossary-aligned.

When a rule has multiple conditions and outcomes, the Product Manager SHOULD
use a markdown decision table instead of long prose.

## Worked examples

### Example backend-only rule

```md
## BR-003 - Closed invoice immutable
- Status: approved
- Rule Class: workflow
- Plain-Language Rule: A closed invoice must not be edited.
- Rationale: Preserve final accounting state.
- Source: product policy
- Trigger: update invoice
- Preconditions: invoice status is `closed`
- Applies To: Invoice.status, Invoice.*
- Valid Outcome: update is rejected unless the invoice is reopened through the approved workflow
- Invalid Outcome: a direct edit to a closed invoice is attempted
- User-Visible Consequence: show a visible save failure explaining that closed invoices are immutable
- Backend Enforcement: required
- Frontend Mirror: none
- Frontend Mirror Reason: server-side truth and workflow authorization are authoritative
- Authoritative Error Message: Closed invoices cannot be edited.
- Examples:
  - valid: reopen invoice, then edit
  - invalid: edit a closed invoice directly
- Backend Test Required: yes
- Frontend Test Required: no
```

### Example input-mirrored rule

```md
## BR-001 - Customer email format
- Status: approved
- Rule Class: validation
- Plain-Language Rule: A customer email address must be syntactically valid before the customer record can be saved.
- Rationale: Prevent unusable contact records.
- Source: product brief
- Trigger: create or update customer
- Preconditions: email is present
- Applies To: Customer.email
- Valid Outcome: save is allowed
- Invalid Outcome: save is rejected
- User-Visible Consequence: show inline validation message on the email field
- Backend Enforcement: required
- Frontend Mirror: input
- Frontend Mirror Reason: cheap single-field syntax check with immediate UX benefit
- Authoritative Error Message: Enter a valid email address.
- Examples:
  - valid: `alex@example.com`
  - invalid: `alex.example.com`
- Backend Test Required: yes
- Frontend Test Required: yes
```

### Example schema-mirrored cross-field rule

```md
## BR-002 - Reservation end after start
- Status: approved
- Rule Class: validation
- Plain-Language Rule: A reservation end time must be later than or equal to its start time.
- Rationale: Prevent impossible reservations.
- Source: product brief
- Trigger: create or update reservation
- Preconditions: start time and end time are both present
- Applies To: Reservation.start_time, Reservation.end_time
- Valid Outcome: save is allowed
- Invalid Outcome: save is rejected
- User-Visible Consequence: show form-level error
- Backend Enforcement: required
- Frontend Mirror: schema
- Frontend Mirror Reason: cheap same-record cross-field check
- Authoritative Error Message: End time must be at or after start time.
- Examples:
  - valid: `10:00 -> 11:00`
  - invalid: `11:00 -> 10:00`
- Backend Test Required: yes
- Frontend Test Required: yes
```

### Example decision-table rule

```md
## BR-012 - Reservation status transition
- Status: approved
- Rule Class: decision-table
- Plain-Language Rule: A reservation may transition to `seated` only when the table is assigned and the reservation time has started.
- Rationale: Prevent impossible seating transitions.
- Source: workflow design
- Trigger: update reservation status
- Preconditions: the requested next status is `seated`
- Applies To: Reservation.status, Reservation.table_id, Reservation.start_time
- Valid Outcome: transition is allowed only in the approved state combination
- Invalid Outcome: transition is rejected
- User-Visible Consequence: show a visible save failure explaining why the transition is blocked
- Backend Enforcement: required
- Frontend Mirror: none
- Frontend Mirror Reason: depends on authoritative workflow state and should remain backend-driven
- Authoritative Error Message: Reservation cannot be marked seated until a table is assigned and the reservation time has started.
- Backend Test Required: yes
- Frontend Test Required: no

| Current Status | Table Assigned | Current Time >= Reservation Time | Allowed Next Status | Result |
| --- | ---: | ---: | --- | --- |
| confirmed | no | yes | seated | reject |
| confirmed | yes | no | seated | reject |
| confirmed | yes | yes | seated | allow |
```
