owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/business-rules.md
  - model-design.md
unresolved:
  - none
last_updated_by: backend

# Rule Mapping

## Required rule traceability table

| Rule ID | Backend fields involved | Backend enforcement location | LogicBank pattern | API behavior | Backend tests | Frontend mirror mode | Frontend mirror location | Frontend tests | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `BR-001` | `MemberProfile.age` | model validators | custom | save rejected | `tests/test_rules.py`, `tests/test_api_contract.py` | `input` | `frontend/src/generated/resources/MemberProfile.tsx` | `frontend/tests/memberProfileValidation.test.tsx` | simple numeric bound check |
| `BR-002` | `MemberProfile.match_pool_id`, `MemberProfile.status_id` | model validators and request cleanup validation | custom | save rejected | `tests/test_bootstrap.py`, `tests/test_api_contract.py` | `form` | `frontend/src/generated/resources/MemberProfile.tsx` | `frontend/tests/memberProfileValidation.test.tsx` | required references |
| `BR-003` | `MemberProfile.completion_score` | model validators | custom | save rejected | `tests/test_rules.py`, `tests/test_api_contract.py` | `input` | `frontend/src/generated/resources/MemberProfile.tsx` | `frontend/tests/memberProfileValidation.test.tsx` | numeric bound check |
| `BR-004` | `MemberProfile.approved_at`, `MemberProfile.is_discoverable` | `rules.py` | `constraint` | save rejected | `tests/test_rules.py`, `tests/test_api_contract.py` | `schema` | `frontend/src/generated/resources/MemberProfile.tsx` | `frontend/tests/memberProfileValidation.test.tsx` | cross-field validation |
| `BR-005` | `MemberProfile.status_code`, `MemberProfile.is_discoverable`, `MemberProfile.discoverable_value` | `rules.py` | `copy` | derived update | `tests/test_rules.py` | `none` | none | none | copied from `ProfileStatus` |
| `BR-006` | `MatchPool.profile_count` | `rules.py` | `count` | derived update | `tests/test_rules.py`, `tests/test_bootstrap.py` | `none` | none | none | aggregate count |
| `BR-007` | `MatchPool.discoverable_profile_count` | `rules.py` | `sum` | derived update | `tests/test_rules.py` | `none` | none | none | sum of `discoverable_value` |
| `BR-008` | `MatchPool.total_completion_score` | `rules.py` | `sum` | derived update | `tests/test_rules.py` | `none` | none | none | sum of `completion_score` |

## Required notes

- declarative LogicBank rules:
  - `BR-004`
  - `BR-005`
  - `BR-006`
  - `BR-007`
  - `BR-008`
- custom Python validation:
  - `BR-001`
  - `BR-002`
  - `BR-003`
- backend-managed fields:
  - `status_code`
  - `is_discoverable`
  - `discoverable_value`
  - `profile_count`
  - `discoverable_profile_count`
  - `total_completion_score`
