owner: product_manager
phase: phase-1-product-definition
status: approved
depends_on:
  - brief.md
  - workflows.md
  - domain-glossary.md
unresolved:
  - none
last_updated_by: architect

# Business Rules Catalog

## Purpose

This catalog defines the approved non-default business rules for the dating
profile operations app.

## Domain Vocabulary Used In Rules

- `discoverable`: profile is eligible to be shown by the dating site
- `approval`: explicit timestamp on `MemberProfile.approved_at`
- `pool aggregate`: derived value maintained on `MatchPool`

## Defaults Not Listed Individually

The catalog does not list ordinary generated CRUD behavior, generic text
search plumbing, or normal framework validation that has no domain-specific
meaning.

## Rule Index

| Rule ID | Title | Class | Frontend Mirror | Status |
| --- | --- | --- | --- | --- |
| `BR-001` | Member age range | validation | `input` | approved |
| `BR-002` | Required pool and status references | validation | `form` | approved |
| `BR-003` | Completion score positive and bounded | validation | `input` | approved |
| `BR-004` | Discoverable profiles require approval timestamp | validation | `schema` | approved |
| `BR-005` | Profile copied discoverability fields follow status | copy | `none` | approved |
| `BR-006` | Match pool profile count | aggregate | `none` | approved |
| `BR-007` | Match pool discoverable profile count | aggregate | `none` | approved |
| `BR-008` | Match pool total completion score | aggregate | `none` | approved |

## BR-001 - Member age range

- Rule ID: `BR-001`
- Title: Member age range
- Status: approved
- Rule Class: validation
- Plain-Language Rule: A member profile age must be between 18 and 99 before
  the record can be saved.
- Rationale: Keep the app focused on adult dating-site profiles and prevent
  obviously invalid values.
- Source: chosen v1 product framing
- Trigger: create or update `MemberProfile`
- Preconditions: `age` is present
- Applies To: `MemberProfile.age`
- Valid Outcome: save is allowed
- Invalid Outcome: save is rejected
- User-Visible Consequence: show inline validation feedback on the age field
- Backend Enforcement: required
- Frontend Mirror: input
- Frontend Mirror Reason: cheap single-field range validation improves form
  clarity
- Authoritative Error Message: Age must be between 18 and 99.
- Examples:
  - valid: `29`
  - invalid: `17`
  - invalid: `120`
- Backend Test Required: yes
- Frontend Test Required: yes

## BR-002 - Required pool and status references

- Rule ID: `BR-002`
- Title: Required pool and status references
- Status: approved
- Rule Class: validation
- Plain-Language Rule: A member profile must reference both a match pool and a
  profile status before it can be saved.
- Rationale: Profiles without an operational grouping or discoverability state
  cannot participate in the workflow.
- Source: workflow design
- Trigger: create or update `MemberProfile`
- Preconditions: none
- Applies To: `MemberProfile.match_pool_id`, `MemberProfile.status_id`
- Valid Outcome: save is allowed
- Invalid Outcome: save is rejected
- User-Visible Consequence: the form shows required-reference feedback and the
  save fails visibly
- Backend Enforcement: required
- Frontend Mirror: form
- Frontend Mirror Reason: form-level required-state feedback helps users fix
  the issue before submit
- Authoritative Error Message: Match pool and status are required.
- Examples:
  - valid: both references selected
  - invalid: pool missing
  - invalid: status missing
- Backend Test Required: yes
- Frontend Test Required: yes

## BR-003 - Completion score positive and bounded

- Rule ID: `BR-003`
- Title: Completion score positive and bounded
- Status: approved
- Rule Class: validation
- Plain-Language Rule: A member profile completion score must be greater than
  0 and at most 100.
- Rationale: The aggregate score should represent a bounded readiness measure.
- Source: product framing
- Trigger: create or update `MemberProfile`
- Preconditions: `completion_score` is present
- Applies To: `MemberProfile.completion_score`
- Valid Outcome: save is allowed
- Invalid Outcome: save is rejected
- User-Visible Consequence: show inline validation on the score field
- Backend Enforcement: required
- Frontend Mirror: input
- Frontend Mirror Reason: cheap numeric bound check with immediate UX value
- Authoritative Error Message: Completion score must be between 1 and 100.
- Examples:
  - valid: `82`
  - invalid: `0`
  - invalid: `140`
- Backend Test Required: yes
- Frontend Test Required: yes

## BR-004 - Discoverable profiles require approval timestamp

- Rule ID: `BR-004`
- Title: Discoverable profiles require approval timestamp
- Status: approved
- Rule Class: validation
- Plain-Language Rule: A discoverable member profile must have an approval
  timestamp.
- Rationale: Site-visible profiles must show they cleared review.
- Source: product policy
- Trigger: create or update `MemberProfile`
- Preconditions: the selected status makes the profile discoverable
- Applies To:
  - `MemberProfile.status_id`
  - `MemberProfile.is_discoverable`
  - `MemberProfile.approved_at`
- Valid Outcome: save is allowed only when `approved_at` is populated
- Invalid Outcome: save is rejected when the profile is discoverable but
  `approved_at` is empty
- User-Visible Consequence: show a visible form-level save failure tied to the
  approval timestamp
- Backend Enforcement: required
- Frontend Mirror: schema
- Frontend Mirror Reason: cross-field validation improves clarity before
  submit
- Authoritative Error Message: Discoverable profiles require approved_at.
- Examples:
  - valid: status `discoverable` with `approved_at`
  - invalid: status `discoverable` without `approved_at`
- Backend Test Required: yes
- Frontend Test Required: yes

## BR-005 - Profile copied discoverability fields follow status

- Rule ID: `BR-005`
- Title: Profile copied discoverability fields follow status
- Status: approved
- Rule Class: copy
- Plain-Language Rule: The profile status code, discoverable flag, and
  discoverable helper value on a member profile must be copied from the
  selected profile status definition.
- Rationale: Keep profile visibility truth aligned with the status catalog.
- Source: reference-resource design
- Trigger: create or update `MemberProfile`
- Preconditions: `status_id` references a valid `ProfileStatus`
- Applies To:
  - `MemberProfile.status_code`
  - `MemberProfile.is_discoverable`
  - `MemberProfile.discoverable_value`
- Valid Outcome: backend-managed fields update automatically
- Invalid Outcome: copied fields drift from the selected status definition
- User-Visible Consequence: copied fields appear read-only and reflect the
  selected status after save
- Backend Enforcement: required
- Frontend Mirror: none
- Frontend Mirror Reason: backend is authoritative and the fields are
  read-only outputs
- Authoritative Error Message: none; fields are derived rather than directly
  user-entered
- Examples:
  - valid: status `discoverable` yields `is_discoverable=true`
  - valid: status `draft` yields `is_discoverable=false`
- Backend Test Required: yes
- Frontend Test Required: no

## BR-006 - Match pool profile count

- Rule ID: `BR-006`
- Title: Match pool profile count
- Status: approved
- Rule Class: aggregate
- Plain-Language Rule: A match pool must keep a derived count of related
  member profiles.
- Rationale: The pool list and dashboard need current workload counts.
- Source: dashboard and list requirements
- Trigger: create, update reparent, or delete `MemberProfile`
- Preconditions: none
- Applies To: `MatchPool.profile_count`
- Valid Outcome: the count reflects current related profiles
- Invalid Outcome: the count drifts from the true related-record total
- User-Visible Consequence: pool list/show pages display current counts
- Backend Enforcement: required
- Frontend Mirror: none
- Frontend Mirror Reason: aggregate truth is backend-managed
- Authoritative Error Message: none; derived field
- Examples:
  - valid: creating a profile increments the target pool count
  - valid: deleting a profile decrements the source pool count
- Backend Test Required: yes
- Frontend Test Required: no

## BR-007 - Match pool discoverable profile count

- Rule ID: `BR-007`
- Title: Match pool discoverable profile count
- Status: approved
- Rule Class: aggregate
- Plain-Language Rule: A match pool must keep a derived count of discoverable
  member profiles by summing `discoverable_value`.
- Rationale: Operations staff need to know how much of a pool is site-ready.
- Source: dashboard and aggregate requirements
- Trigger: create, update status change, reparent, or delete `MemberProfile`
- Preconditions: none
- Applies To: `MatchPool.discoverable_profile_count`
- Valid Outcome: the count reflects discoverable profiles in the pool
- Invalid Outcome: discoverable totals drift from status-driven reality
- User-Visible Consequence: pool list/show pages display current discoverable
  totals
- Backend Enforcement: required
- Frontend Mirror: none
- Frontend Mirror Reason: aggregate truth is backend-managed
- Authoritative Error Message: none; derived field
- Examples:
  - valid: changing a profile to discoverable increments the pool total
  - valid: moving a discoverable profile between pools updates both pools
- Backend Test Required: yes
- Frontend Test Required: no

## BR-008 - Match pool total completion score

- Rule ID: `BR-008`
- Title: Match pool total completion score
- Status: approved
- Rule Class: aggregate
- Plain-Language Rule: A match pool must keep a derived sum of member profile
  completion scores.
- Rationale: The pool should expose a simple readiness total without custom
  reporting.
- Source: aggregate requirements
- Trigger: create, update score change, reparent, or delete `MemberProfile`
- Preconditions: none
- Applies To: `MatchPool.total_completion_score`
- Valid Outcome: the aggregate sum matches the related profile scores
- Invalid Outcome: pool totals drift after edits or reparenting
- User-Visible Consequence: pool list/show pages expose a live readiness total
- Backend Enforcement: required
- Frontend Mirror: none
- Frontend Mirror Reason: aggregate truth is backend-managed
- Authoritative Error Message: none; derived field
- Examples:
  - valid: editing a profile score updates the parent pool total
  - valid: deleting a profile reduces the total
- Backend Test Required: yes
- Frontend Test Required: no
