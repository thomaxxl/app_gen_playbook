owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
unresolved:
  - none
last_updated_by: architect

# Test Obligations

## Backend obligations

- validate that `/docs`, `/jsonapi.json`, `/ui/admin/admin.yaml`, and exposed
  resource endpoints exist
- validate seed/bootstrap idempotency
- validate derived copied fields and pool aggregates after create, update,
  delete, and reparent
- validate approval constraint rejection and required-reference rejection

## Frontend obligations

- run `npm run check`
- run `npm run test`
- run `npm run build`
- run Playwright smoke coverage for:
  - `/admin-app/#/Home`
  - primary resource route for `MemberProfile`

## Runtime validation obligations

- validate final discovered SAFRS endpoints and wire types
- validate generated resource wrappers match the approved naming table
- validate `Home` is the visible primary entry route
