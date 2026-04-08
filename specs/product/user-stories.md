owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - brief.md
  - user-journeys.md
  - workflows.md
  - sample-data.md
  - acceptance-criteria.md
  - traceability-matrix.md
unresolved:
  - replace with run-specific user stories
last_updated_by: playbook

# User Story Catalog

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/user-stories.md`.

User stories are not prose decoration. They are the authoritative scope
contract that drives workflows, custom pages, routes, reviews, tests, and
acceptance.

The story catalog MUST stay focused on user need, scope priority, and
testability. Implementation mapping belongs in
`traceability-matrix.md`, not in the story core.

## Decision rule

The real artifact MUST separate:

- breadth: actor-by-capability coverage across the first-version scope
- story core: the user-facing outcome, primary journey anchor, priority, and
  independent test for each story
- depth: detailed scenario coverage for current-release stories
- traceability: workflow/rule/page/route/evidence mapping in
  `traceability-matrix.md`

## Story priority model

Canonical story priority is:

- `P1` = current-release core story
- `P2` = current-release non-core or next-in-line story
- `P3` = later-release or stretch story

If the run needs commitment language, add:

- `Delivery Class`: `must`, `should`, or `could`

New artifacts MUST use `P1`/`P2`/`P3` in the `Priority` column and keep
commitment language in `Delivery Class`. Do not put `must`/`should`/`could`
directly in the `Priority` column for new story catalogs.

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
Matrix` heading. Use `yes` or `no` values only. This matrix is the coarse
human-readable breadth view; it is not the canonical story ledger.

| Actor | Discover/Search | Create/Intake | Inspect/Detail | Edit/Maintain | Workflow/Approval | Exception/Recovery | Reporting/Export | Admin/Setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Requester | yes | yes | yes | yes | no | yes | no | no |
| Approver | yes | no | yes | no | yes | yes | yes | no |
| Operator | yes | yes | yes | yes | yes | yes | yes | yes |

## Capability Coverage

The real artifact MUST include this normalized table under the
`## Capability Coverage` heading. This is the canonical machine-validated
source for actor/capability breadth coverage.

| Actor | Capability Band | Covered by Story IDs |
| --- | --- | --- |
| Requester | Discover/Search | US-001 |
| Requester | Create/Intake | US-002 |
| Approver | Workflow/Approval | US-010 |
| Approver | Exception/Recovery | US-011 |

The normalized `Capability Coverage` table is authoritative when the compiler
audits breadth coverage. The coarse `Coverage Matrix` is a summary view and
MUST stay aligned with that normalized ledger.

## Story Index

The real artifact MUST include this exact table under the `## Story Index`
heading.

| Story ID | Title | Actor | Priority | Delivery Class | Release | Story Type | Primary Journey ID | Story Statement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| US-010 | Approver reviews pending requests | Approver | P1 | must | R1 | approval | J-010 | As an Approver, I review pending requests and either approve or reject them with an audit note. |

Rules:

- keep the story core user-facing and testable
- every current-release story MUST have a `Primary Journey ID`
- later-release stories MAY use `none` only when the journey is intentionally
  deferred
- `Primary Journey ID` MUST point to a real journey in `user-journeys.md`
- do not put workflow IDs, rule IDs, page IDs, route IDs, permission mapping,
  or sample-data mapping in the story index
- do not duplicate `Why this priority` or `Independent Test` in the story
  index; the canonical source for those fields is the current-release story
  block under `## User Scenarios & Testing`
- if a current-release story needs implementation linkage, record it in
  `traceability-matrix.md`

## User Scenarios & Testing

The real artifact MUST include a `### <Story ID> - <short title>` subsection
for every current-release story. Every current-release story block MUST be a
spec-kit-compatible core record of the user journey and independent test.

Every current-release story block MUST include:

- `**Actor**:`
- `**Story Type**:`
- `**Release**:`
- `**Why this priority**:`
- `**Independent Test**:`
- `**Acceptance Scenarios**:`
- `**Edge Cases**:`

Each `Acceptance Scenarios` section MUST include at least one concrete
`Given / When / Then` scenario.

For current-release stories, `Why this priority` and `Independent Test` in
this block are the canonical story-core record. Do not duplicate or maintain a
second canonical copy of those fields elsewhere.

Higher-depth story blocks are required for:

- every current-release `P1` story
- every current-release workflow-heavy `P2` story

Higher-depth story blocks MUST also include:

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

### US-010 - Approver reviews pending requests (Priority: P1)
**Actor**: Approver
**Story Type**: approval
**Release**: R1

As an Approver, I review pending requests and either approve or reject them
with an audit note.

**Why this priority**: Pending approvals are the gating step that determines
whether work can continue, so this flow must be reliable in the first release.
**Independent Test**: Create or locate one pending request assigned to the
current approver, approve it, and confirm the queue, detail view, and audit
trail all reflect the decision without relying on a second story.

**Acceptance Scenarios**:
1. **Given** a pending request assigned to the approver **When** the approver
   opens the detail view and clicks approve **Then** the request becomes
   approved, disappears from the pending queue, and records an audit note.
2. **Given** a pending request assigned to the approver **When** the approver
   rejects it without a required reason **Then** the action is blocked with a
   clear validation message.

**Edge Cases**:
- the queue is empty and must explain the next available action
- another user has already resolved the request before approval is submitted

Context / trigger: The approver opens the pending approvals queue from the
home dashboard.
Preconditions: At least one request is in `pending_approval` state and is
assigned to the current approver.
Happy path: The approver opens the request, reviews the details, approves it,
and the queue updates immediately.
Alternate paths: The approver rejects the request with a required rejection
reason, or requests clarification and leaves the request pending.
Negative / validation paths: An approval attempt without a required comment or
against an already-closed request is blocked with a clear message.
Empty-state expectation: When no items are pending, the queue shows a usable
empty-state message and next-step guidance.
Permission constraints: Only assigned approvers or supervisors can action the
request.
Audit / notification expectation: Approval or rejection writes an audit record
and triggers the standard notification.
Non-goals: Bulk approval and delegated approval are out of scope for R1.
Required evidence: Review screenshots for the queue, approval detail view, and
audit entry plus a live validation note for the approval flow.

## Cross-Story Edge Cases

Use this section for edge conditions that affect multiple stories and do not
belong to only one user journey.

## Open Questions

Keep only unresolved product decisions here. Do not use this section as a
parking lot for implementation work that belongs in Architecture, UX, Backend,
or DevOps artifacts.
