# Backend Role Summary

Use this role for models, relationships, SAFRS exposure, bootstrap strategy,
LogicBank rules, backend tests, route discovery, and backend verification.

Always load:

- `global-core.md`
- `process-core.md`
- one stage-specific Backend read set:
  - `../../process/read-sets/backend-design-core.md`
  - `../../process/read-sets/backend-implementation-core.md`
  - `../../process/read-sets/backend-change-delta.md`

This role controls backend-design artifacts and backend implementation. It
does not invent product scope, UX behavior, or packaging decisions.

Load UX or optional feature-pack material only when the current task requires
it and the load plan allows it.

Backend decision tree:

- persisted DB row data => SAFRS resource
- DB relationship => ORM relationship plus SAFRS relationship URL/include
- computed resource field => `jsonapi_attr`
- explicit operation => `jsonapi_rpc`
- anything else => documented exception such as `JABase`

Full docs:

- `../../roles/backend.md`
- `../../../specs/contracts/backend/README.md`
- `../../../specs/contracts/rules/README.md`
