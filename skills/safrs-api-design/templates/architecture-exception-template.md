# SAFRS API Exception Record

Use this only when a DB-backed API need cannot stay inside the normal SAFRS lanes.

## Request summary

- Feature or screen:
- Consumer:
- Requested behavior:
- Persisted DB-backed data involved:

## Proposed custom surface

- Proposed endpoint or service surface:
- Request/response summary:
- Why it exists:

## Rejected SAFRS lanes

### 1. Resource lane rejected because

-

### 2. Relationship lane rejected because

-

### 3. `include=...` lane rejected because

-

### 4. `@jsonapi_attr` lane rejected because

-

### 5. `@jsonapi_rpc` lane rejected because

-

## Why this is a valid exception

-

## Replacement contract

- Canonical caller:
- Stability expectations:
- Query/filter/sort/include expectations:
- Error behavior:
- Auth/visibility expectations:

## SAFRS surface that still remains canonical

- Resource paths that still exist:
- Relationship paths that still exist:
- Include paths that still exist:
- Why the custom surface is supplemental rather than a silent replacement:

## Run-owned artifact updates required

- `architecture/integration-boundary.md`
- `architecture/data-sourcing-contract.md`
- `backend-design/resource-exposure-policy.md`
- `backend-design/relationship-map.md`
- `backend-design/query-behavior.md`
- `backend-design/test-plan.md`

## Evidence required

- live `/jsonapi.json` proof:
- live relationship or include proof:
- custom endpoint proof:
- automated test coverage:
- architecture approval note:

## Approval

- Architect:
- Backend:
- Review date:
