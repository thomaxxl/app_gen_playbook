owner: product_manager
phase: phase-1-product-definition
status: approved
depends_on:
  - brief.md
  - input-interpretation.md
unresolved:
  - none
last_updated_by: architect

# Resource Inventory

## MatchPool

- purpose: group profiles by market or launch cohort so staff can manage
  inventory and discoverability at a meaningful operational level
- primary users: Profile Operations Manager
- display key: `code`
- core product fields:
  - `code`
  - `name`
  - `owner_name`
  - `profile_count`
  - `discoverable_profile_count`
  - `total_completion_score`
- key relationships:
  - one-to-many `profiles`
- CRUD expectations:
  - list: yes
  - show: yes
  - create: yes
  - edit: yes
  - delete: yes
- search, filter, sort:
  - search by `code`, `name`, `owner_name`
  - sort by derived aggregate fields and identifiers
- classification: core aggregate parent resource
- rule touchpoints:
  - `BR-006`
  - `BR-007`
  - `BR-008`
- generated-page sufficiency:
  - generated CRUD is sufficient

## MemberProfile

- purpose: represent a dating-site member record that can be reviewed,
  approved, and surfaced as discoverable
- primary users:
  - Profile Operations Manager
  - Trust and Safety Coordinator
- display key: `display_name`
- core product fields:
  - `display_name`
  - `city`
  - `age`
  - `dating_intent`
  - `completion_score`
  - `approved_at`
  - `match_pool_id`
  - `status_id`
  - `status_code`
  - `is_discoverable`
  - `discoverable_value`
- key relationships:
  - many-to-one `match_pool`
  - many-to-one `status`
- CRUD expectations:
  - list: yes
  - show: yes
  - create: yes
  - edit: yes
  - delete: yes
- search, filter, sort:
  - search by `display_name`, `city`, `dating_intent`
  - filter by `match_pool_id`, `status_id`, `is_discoverable`
  - sort by `display_name`, `city`, `age`, `completion_score`, `approved_at`
- classification: core CRUD resource
- rule touchpoints:
  - `BR-001`
  - `BR-002`
  - `BR-003`
  - `BR-004`
  - `BR-005`
- generated-page sufficiency:
  - generated CRUD is sufficient

## ProfileStatus

- purpose: define the discoverability state catalog that drives copied fields
  on profiles
- primary users:
  - Profile Operations Manager
  - Trust and Safety Coordinator
- display key: `label`
- core product fields:
  - `code`
  - `label`
  - `is_discoverable`
  - `discoverable_value`
- key relationships:
  - one-to-many `profiles`
- CRUD expectations:
  - list: yes
  - show: yes
  - create: yes
  - edit: yes
  - delete: yes
- search, filter, sort:
  - search by `code`, `label`
  - sort by `code`, `label`, `is_discoverable`
- classification: reference/status resource
- rule touchpoints:
  - `BR-005`
- generated-page sufficiency:
  - generated CRUD is sufficient
