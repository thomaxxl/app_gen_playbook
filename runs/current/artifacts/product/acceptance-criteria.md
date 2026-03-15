owner: product_manager
phase: phase-1-product-definition
status: approved
depends_on:
  - brief.md
unresolved:
  - none
last_updated_by: architect

# Acceptance Criteria

## Workflow acceptance

| ID | Criterion | Traceability |
| --- | --- | --- |
| `AC-001` | Users can create, edit, and delete `MatchPool` records from generated CRUD pages. | `US-001`, `WF-001`, `MatchPool` |
| `AC-002` | Users can create and edit `MemberProfile` records with pool and status references from generated CRUD pages. | `US-002`, `WF-002`, `MemberProfile` |
| `AC-003` | Users can reach the main workflow from `Home` without relying on sidebar discovery first. | `US-005`, `WF-003`, `HOME-001` |

## CRUD acceptance

| ID | Criterion | Traceability |
| --- | --- | --- |
| `AC-004` | `MatchPool`, `MemberProfile`, and `ProfileStatus` each support list, show, create, edit, and delete in the app. | `resource-behavior-matrix.md` |
| `AC-005` | Reference fields display readable related labels instead of raw ids in generated views. | `WF-002`, `MemberProfile`, `ProfileStatus` |

## Custom-page acceptance

| ID | Criterion | Traceability |
| --- | --- | --- |
| `AC-006` | `Home` shows app purpose, proof cues, and a visible primary CTA. | `US-005`, `HOME-001` |

## Business-rule acceptance

| ID | Criterion | Traceability |
| --- | --- | --- |
| `AC-007` | Invalid ages and completion scores are rejected. | `BR-001`, `BR-003` |
| `AC-008` | Missing `match_pool_id` or `status_id` rejects a profile save. | `BR-002` |
| `AC-009` | Discoverable profiles without `approved_at` are rejected. | `BR-004` |
| `AC-010` | Pool aggregates and copied status fields update automatically after create, update, delete, and reparent actions. | `BR-005`, `BR-006`, `BR-007`, `BR-008` |

## Search acceptance

| ID | Criterion | Traceability |
| --- | --- | --- |
| `AC-011` | Profile search supports name, city, and intent lookups through the generated list search entry. | `US-006`, `WF-002`, `MemberProfile` |
