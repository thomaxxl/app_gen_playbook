owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - brief.md
  - research-notes.md
  - domain-glossary.md
  - workflows.md
  - business-rules.md
unresolved:
  - replace with run-specific conceptual domain model
last_updated_by: playbook

# Conceptual Domain Model Template

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/conceptual-domain-model.md`.

This artifact is the authoritative business-facing conceptual model for the
run.

It MUST define business concepts, relationships, lifecycle/state models, and
business events without collapsing them into database tables, ORM classes,
SAFRS resources, route names, or implementation-only storage details.

It MUST NOT include:

- SQL table names
- column names
- foreign-key names
- ORM class names
- endpoint names
- SAFRS exposure choices
- implementation-only derived fields

## Required top-level sections

The run-owned file MUST include these sections in this order:

1. `Purpose and scope`
2. `Domain areas`
3. `Business concepts`
4. `Concept relationships`
5. `Lifecycle models`
6. `Business events`
7. `Concept-to-resource hints`
8. `Deferred or ambiguous concepts`

## Domain areas

The real artifact MUST include a table with at least these columns:

| Area ID | Name | Purpose | Notes |
| --- | --- | --- | --- |
| `DA-001` | Requests | Intake and lifecycle of requests | Replace this row |

Use domain areas to group related concepts. If the same word means different
things in different areas, record that explicitly here.

## Business concepts

The real artifact MUST include a table with at least these columns:

| Concept ID | Name | Area ID | Kind | Definition | Business identity | Lifecycle ID | Primary actors | Workflow IDs | Rule IDs | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `C-001` | Request | `DA-001` | entity | Replace this row | request number | `LC-001` | requester, approver | `WF-001` | `BR-001` | Replace this row |

Recommended `Kind` values:

- `entity`
- `transaction`
- `reference-data`
- `value-object`
- `policy`
- `role`
- `process-artifact`

## Concept relationships

The real artifact MUST include a table with at least these columns:

| Relationship ID | From Concept | To Concept | Meaning | Cardinality | Rule IDs | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `REL-001` | `C-001` | `C-002` | Replace this row | one-to-many | `BR-010` | Replace this row |

This section describes business meaning, not FK or join-table design.

## Lifecycle models

For every concept with meaningful state, the real artifact MUST define a
lifecycle table.

### Example lifecycle section

#### LC-001 - Request lifecycle

| State | Meaning | Entered by | Exit paths | Rule IDs | Workflow IDs |
| --- | --- | --- | --- | --- | --- |
| draft | Replace this row | create request | submit, cancel | `BR-001` | `WF-001` |

## Business events

The real artifact MUST include a table with at least these columns:

| Event ID | Name | Trigger | Concepts affected | State change | Rule IDs | Workflow IDs | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `EV-001` | Request submitted | requester submits request | `C-001` | `draft -> submitted` | `BR-011` | `WF-001` | Replace this row |

These are business-facing events. They are not automatically the same thing as
implementation-level domain events, integration events, audit rows, or backend
triggers.

## Concept-to-resource hints

The real artifact MUST include a table with at least these columns:

| Concept ID | Likely application shape | Candidate resource name(s) | Notes |
| --- | --- | --- | --- |
| `C-001` | first-class resource | Request | Replace this row |

Allowed `Likely application shape` examples:

- `first-class resource`
- `singleton/settings`
- `reference/status resource`
- `supporting transaction record`
- `read-model/dashboard only`
- `deferred`

This section is advisory for downstream roles. It MUST stay business-facing
and MUST NOT become API or ORM design.

## Deferred or ambiguous concepts

The real artifact MUST explicitly list:

- concepts that are intentionally deferred
- concepts that appear in the brief but remain ambiguous
- terms that need a context split because they mean different things in
  different domain areas
