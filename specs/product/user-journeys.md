owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - brief.md
  - user-stories.md
  - workflows.md
  - business-rules.md
  - conceptual-domain-model.md
unresolved:
  - replace with run-specific user journeys
last_updated_by: playbook

# User Journey Catalog

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/user-journeys.md`.

This artifact is the authoritative human-readable journey catalog for the run.

A user journey is an end-to-end, user-goal-centered path through the
application. It explains:

- who is trying to achieve something
- what outcome they want
- how they move through the experience at a human level
- where alternate, approval, failure, or recovery paths appear
- what makes the journey successful or unsuccessful

A journey is not:

- a page inventory
- a route inventory
- a backend flow chart
- a low-level workflow transition list
- a database process map
- a copy of the traceability matrix

## Required top-level sections

The run-owned file MUST include these sections in this order:

1. `# User Journey Catalog`
2. `## Decision Rule`
3. `## Journey Taxonomy`
4. `## Journey Index`
5. `## Journey Details`
6. `## Journey Coverage Summary`
7. `## Deferred / Later-Release Journeys`
8. `## Open Questions`

## Decision Rule

The real artifact MUST keep these layers distinct:

- user stories = independently testable slices of value
- workflows = stepwise business and operational flows
- user journeys = human-centered end-to-end paths that may span multiple
  stories or workflows
- traceability = mapping from story scope to implementation and review
  obligations
- acceptance = explicit contract for what must be true in the delivered app

Do not collapse journeys into stories or workflows.

## Journey Taxonomy

The real artifact MUST use one of these canonical `Journey Class` values:

- `onboarding-intake`
- `primary-transaction`
- `review-approval`
- `exception-recovery`
- `reporting-oversight`
- `admin-setup`
- `cross-role-collaboration`

Do not invent free-form journey classes unless the playbook is explicitly
extended.

## Journey Index

The real artifact MUST include this exact table under the `## Journey Index`
heading.

| Journey ID | Title | Primary Actor | Supporting Actors | Journey Class | Release | Priority | Entry Trigger | Successful Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J-001 | Requester submits a request | Requester | Approver | primary-transaction | R1 | P1 | Requester starts a new request | A valid request is submitted and ready for review. |

Rules:

- journey IDs MUST stay stable and use `J-001`, `J-002`, ... style numbering
- every current-release journey MUST appear in the index
- every current-release journey MUST have a real supporting detailed block
- later-release journeys MAY remain index-only when the deferral is explicit

## Journey Details

For every current-release journey, the real artifact MUST include a
`### <Journey ID> - <short title>` block with this exact field set:

- `**Primary Actor**:`
- `**Supporting Actors**:`
- `**Journey Class**:`
- `**Release**:`
- `**Why this journey matters**:`
- `**Preconditions**:`
- `**Entry Trigger**:`
- `**Happy Path**:`
- `**Alternate Paths**:`
- `**Failure / Recovery Paths**:`
- `**Successful Outcome**:`
- `**Independent Journey Test**:`
- `**Related Story IDs**:`
- `**Related Workflow IDs**:`
- `**Related Rule IDs**:`
- `**Related Business Event IDs**:`
- `**Notes for UX / Visibility**:`

Worked example:

### J-001 - Requester submits a new request
- **Primary Actor**: Requester
- **Supporting Actors**: Approver
- **Journey Class**: primary-transaction
- **Release**: R1
- **Why this journey matters**: Intake is the first meaningful promise of the
  product and must be understandable to a new requester.
- **Preconditions**: The requester is authorized to create a request and the
  required intake fields are available.
- **Entry Trigger**: The requester starts a new request from the primary entry
  surface.
- **Happy Path**: The requester opens intake, supplies the required fields,
  reviews the summary, and submits successfully.
- **Alternate Paths**: The requester saves a draft or pauses to gather missing
  supporting data.
- **Failure / Recovery Paths**: Validation failures explain what must change;
  denied submission or missing required approvals show the next recovery step.
- **Successful Outcome**: The request is submitted and becomes available for
  review.
- **Independent Journey Test**: A requester can start from the delivered
  navigation, complete intake with valid required fields only, and reach the
  submitted state without hidden reviewer steps.
- **Related Story IDs**: US-001, US-002
- **Related Workflow IDs**: WF-001
- **Related Rule IDs**: BR-001, BR-004
- **Related Business Event IDs**: EV-001
- **Notes for UX / Visibility**: The path must make draft-versus-submit status
  obvious and explain blocked validation states clearly.

## Journey Coverage Summary

The real artifact MUST summarize:

- which primary actors have current-release journeys
- which journey classes are represented in the current release
- which current-release journeys require alternate, approval, or recovery
  coverage

## Deferred / Later-Release Journeys

List intentionally deferred or later-release journeys explicitly instead of
leaving them implied.

## Open Questions

Use this section only for unresolved product questions about journey intent,
coverage, or user-visible ambiguity.

## Authoring Rules

The run-owned artifact MUST follow these rules:

- journey descriptions must stay user-centered and readable
- a journey must describe end-to-end intent, not just page clicks
- every current-release journey must include at least one alternate or recovery
  path when that path is realistic
- detailed implementation mapping belongs in `traceability-matrix.md`, not in
  journey prose
- every current-release journey must reference real story IDs and workflow IDs
- if a journey touches approval, exception, or recovery, that must be explicit
  in the detailed block
