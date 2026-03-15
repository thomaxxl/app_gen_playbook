owner: product_manager
phase: phase-1-product-definition
status: approved
depends_on:
  - workflows.md
  - business-rules.md
unresolved:
  - none
last_updated_by: architect

# Sample Data

## Reference records

### ProfileStatus

- `draft` / `Draft` / `is_discoverable=false` / `discoverable_value=0`
- `review` / `In Review` / `is_discoverable=false` / `discoverable_value=0`
- `discoverable` / `Discoverable` / `is_discoverable=true` /
  `discoverable_value=1`

## Canonical happy-path scenarios

- `MatchPool`:
  - `SEA-SINGLES` / `Seattle Singles` / owner `Mina Cole`
  - `ATX-NEW` / `Austin New Members` / owner `Ravi Hale`
- `MemberProfile`:
  - `Lena Ortiz`, Seattle, `29`, `Long-term dating`, score `82`,
    pool `SEA-SINGLES`, status `discoverable`, approved timestamp present
  - `Maya Chen`, Seattle, `31`, `Serious relationship`, score `74`,
    pool `SEA-SINGLES`, status `draft`, no approval timestamp
  - `Noah Patel`, Austin, `34`, `New connections`, score `67`,
    pool `ATX-NEW`, status `review`, no approval timestamp
  - `Avery Brooks`, Austin, `27`, `Long-term dating`, score `91`,
    pool `ATX-NEW`, status `discoverable`, approved timestamp present

## Boundary conditions

- age `18`
- age `99`
- completion score `1`
- completion score `100`

## Invalid or negative scenarios

- age `17`
- completion score `0`
- discoverable profile without `approved_at`
- missing `match_pool_id`
- missing `status_id`

## Workflow-specific records

- at least one discoverable and one non-discoverable profile per pool
- enough records to prove pool aggregate changes on reparent and delete

## Rule-specific records

- a profile changed from `draft` to `discoverable`
- a profile moved from `SEA-SINGLES` to `ATX-NEW`
- a profile deleted from a pool after creation

## Search test records

- two profiles in the same city with different statuses
- intent values that allow text search hits on `dating_intent`
