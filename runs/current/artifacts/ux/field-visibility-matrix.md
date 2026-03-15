owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
  - ../product/business-rules.md
unresolved:
  - none
last_updated_by: frontend

# Field Visibility Matrix

| Resource | Field | Label | Section/group | Help text | Placeholder or prompt intent | Inline validation hint | Frontend mirror rule ID | List | Show | Create | Edit | Readonly | Hidden | Display format | Searchable | Sortable | Reference-label behavior | Widget intent | Form span | Rows | Content or microcopy notes | Reason when non-default |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MatchPool` | `id` | ID | system | none | none | none | none | no | no | no | no | yes | yes | hidden | no | no | n/a | hidden | 3 | 1 | internal primary key | default hidden |
| `MatchPool` | `code` | Pool Code | identity | short unique operational code | e.g. `SEA-SINGLES` | required | none | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text | 4 | 1 | use code as main list identity | non-default label |
| `MatchPool` | `name` | Name | identity | human-readable pool name | e.g. `Seattle Singles` | required | none | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text | 8 | 1 | standard descriptive name | none |
| `MatchPool` | `owner_name` | Owner | operations | person accountable for the pool | e.g. `Mina Cole` | required | none | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text | 6 | 1 | helps users identify stewardship | none |
| `MatchPool` | `profile_count` | Profiles | aggregates | derived count of profiles in pool | none | none | none | yes | yes | no | no | yes | no | number | no | yes | n/a | readonly number | 3 | 1 | show as proof cue in list/show | derived aggregate |
| `MatchPool` | `discoverable_profile_count` | Discoverable Profiles | aggregates | derived count of discoverable profiles | none | none | none | yes | yes | no | no | yes | no | number | no | yes | n/a | readonly number | 3 | 1 | keep visible in lists | derived aggregate |
| `MatchPool` | `total_completion_score` | Total Completion Score | aggregates | derived sum of profile completion scores | none | none | none | yes | yes | no | no | yes | no | number | no | yes | n/a | readonly number | 3 | 1 | operational readiness total | derived aggregate |
| `MemberProfile` | `id` | ID | system | none | none | none | none | no | no | no | no | yes | yes | hidden | no | no | n/a | hidden | 3 | 1 | internal primary key | default hidden |
| `MemberProfile` | `display_name` | Display Name | identity | member-facing display name | e.g. `Lena Ortiz` | required | none | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text | 6 | 1 | primary record label | non-default label |
| `MemberProfile` | `city` | City | basics | location label used in review and search | e.g. `Seattle` | required | none | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text | 3 | 1 | keep compact in form layout | none |
| `MemberProfile` | `age` | Age | basics | adult age in years | e.g. `29` | must be 18-99 | `BR-001` | yes | yes | yes | yes | no | no | number | no | yes | n/a | number | 3 | 1 | compact numeric field | mirrored range validation |
| `MemberProfile` | `dating_intent` | Dating Intent | basics | short description of what the member wants | e.g. `Long-term dating` | required | none | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text | 12 | 3 | use multiline input for clarity | wide text field |
| `MemberProfile` | `completion_score` | Completion Score | review | profile readiness score | e.g. `82` | must be 1-100 | `BR-003` | yes | yes | yes | yes | no | no | number | no | yes | n/a | number | 3 | 1 | keep near status fields | mirrored numeric bound |
| `MemberProfile` | `approved_at` | Approved At | review | required when status is discoverable | none | required for discoverable profiles | `BR-004` | yes | yes | yes | yes | no | no | datetime | no | yes | n/a | datetime | 6 | 1 | show clear review semantics | cross-field rule |
| `MemberProfile` | `match_pool_id` | Match Pool | references | operational pool assignment | select a pool | required | `BR-002` | yes | yes | yes | yes | no | no | reference | no | yes | show `MatchPool.code` | reference autocomplete | 6 | 1 | label should resolve to pool code | required reference |
| `MemberProfile` | `status_id` | Profile Status | references | discoverability state | select a status | required | `BR-002` | yes | yes | yes | yes | no | no | reference | no | yes | show `ProfileStatus.label` | reference autocomplete | 6 | 1 | label should resolve to status label | required reference |
| `MemberProfile` | `status_code` | Status Code | derived | copied from selected status | none | none | none | no | yes | no | no | yes | no | text | no | yes | n/a | readonly text | 3 | 1 | visible only on show for debugging clarity | copied field |
| `MemberProfile` | `is_discoverable` | Discoverable | derived | copied visibility boolean | none | none | none | yes | yes | no | no | yes | no | boolean | no | yes | n/a | readonly boolean | 3 | 1 | keep visible in list/show | copied field |
| `MemberProfile` | `discoverable_value` | Discoverable Value | derived | numeric helper for aggregates | none | none | none | no | yes | no | no | yes | yes | hidden | no | no | n/a | hidden | 3 | 1 | internal helper field | hide because user-facing boolean already exists |
| `ProfileStatus` | `id` | ID | system | none | none | none | none | no | no | no | no | yes | yes | hidden | no | no | n/a | hidden | 3 | 1 | internal primary key | default hidden |
| `ProfileStatus` | `code` | Code | identity | stable internal status code | e.g. `discoverable` | required | none | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text | 4 | 1 | compact code field | none |
| `ProfileStatus` | `label` | Label | identity | user-facing status label | e.g. `Discoverable` | required | none | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text | 8 | 1 | shown in references | none |
| `ProfileStatus` | `is_discoverable` | Discoverable | semantics | whether the status allows site visibility | none | required | none | yes | yes | yes | yes | no | no | boolean | no | yes | n/a | boolean toggle | 4 | 1 | clear boolean label required | none |
| `ProfileStatus` | `discoverable_value` | Discoverable Value | semantics | numeric helper used for pool aggregate sums | use `1` for discoverable and `0` otherwise | required | none | yes | yes | yes | yes | no | no | number | no | yes | n/a | number | 4 | 1 | keep explicit to support aggregate transparency | none |
