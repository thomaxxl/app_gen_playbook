owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - brief.md
  - workflows.md
  - sample-data.md
  - acceptance-criteria.md
unresolved:
  - replace with run-specific user stories
last_updated_by: playbook

# User Story Catalog

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/user-stories.md`.

User stories are not prose decoration. They are the authoritative scope
contract that drives workflows, custom pages, routes, reviews, tests, and
acceptance.

## Decision rule

The real artifact MUST separate:

- breadth: actor-by-capability coverage across the first-version scope
- depth: scenario detail for every `must` story and every workflow-heavy
  `should` story

Every primary actor MUST be represented in the coverage matrix. Every `must`
story MUST include happy path, alternate path, negative or validation path,
empty-state expectation, and permission context. Workflow-heavy `should`
stories MUST include the same detailed scenario structure.

## Story type taxonomy

The real artifact MUST use this taxonomy for `Story Type`:

- `crud`
- `workflow-transition`
- `approval`
- `reporting-search`
- `exception-recovery`
- `admin-configuration`
- `integration-import-export`
- `notification-audit`

If the author has not clearly described an edge type, choose the closest type
above instead of inventing a new label.

## Coverage Matrix

The real artifact MUST include this exact table first under the `## Coverage
Matrix` heading. Use `yes` or `no` values and list the covering story IDs in
`Covered by`.

| Actor | Discover/Search | Create/Intake | Inspect/Detail | Edit/Maintain | Workflow/Approval | Exception/Recovery | Reporting/Export | Admin/Setup | Covered by |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Requester | yes | yes | yes | yes | no | yes | no | no | US-001, US-002, US-005 |
| Approver | yes | no | yes | no | yes | yes | yes | no | US-010, US-011 |
| Operator | yes | yes | yes | yes | yes | yes | yes | yes | US-020, US-021 |

## Story Index

The real artifact MUST include this exact table under the `## Story Index`
heading.

| Story ID | Epic | Actor | Story Type | Priority | Release | Frequency | Criticality | Story Statement | Workflow IDs | Rule IDs | Resource IDs | Page IDs | Route IDs | Permission Context | Sample Data IDs | Acceptance IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| US-010 | Approvals | Approver | approval | must | R1 | daily | high | As an Approver, I review pending requests and either approve or reject them with an audit note. | WF-010 | BR-010 | Request, Approval | PAGE-006 | N007 | approver can review only assigned requests | SD-010 | AC-010 |

## Detailed Stories

The real artifact MUST include a `### <Story ID> - <short title>` subsection
for every `must` story and every workflow-heavy `should` story. Each required
detail section MUST include the exact fields below:

- `Context / trigger:`
- `Preconditions:`
- `Happy path:`
- `Alternate paths:`
- `Negative / validation paths:`
- `Empty-state expectation:`
- `Permission constraints:`
- `Audit / notification expectation:`
- `Non-goals:`
- `Required evidence:`

Worked example:

### US-010 - Approver reviews pending request

- Context / trigger: The approver opens the pending approvals queue from the
  home dashboard.
- Preconditions: At least one request is in `pending_approval` state and is
  assigned to the current approver.
- Happy path: The approver opens the request, reviews the details, approves
  it, and the queue updates immediately.
- Alternate paths: The approver rejects the request with a required rejection
  reason, or requests clarification and leaves the request pending.
- Negative / validation paths: An approval attempt without a required comment
  or against an already-closed request is blocked with a clear message.
- Empty-state expectation: When no items are pending, the queue shows a usable
  empty-state message and next-step guidance.
- Permission constraints: Only assigned approvers or supervisors can action
  the request.
- Audit / notification expectation: Approval or rejection writes an audit
  record and triggers the standard notification.
- Non-goals: Bulk approval and delegated approval are out of scope for R1.
- Required evidence: Review screenshots for the queue, approval detail view,
  and audit entry plus a live validation note for the approval flow.
