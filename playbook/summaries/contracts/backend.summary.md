# Backend Contract Summary

Load this when a task touches backend runtime, exposure, startup, or API
verification behavior.

The backend contract controls:

- the hard rule that ordinary DB-backed entities and relationships use mapped
  SQLAlchemy ORM plus SAFRS resources and relationship URLs as the canonical
  API surface
- SAFRS/FastAPI startup order
- model naming and exposure rules
- the default rule that appropriate DB-backed tables and relationships are
  exposed through SAFRS JSON:API resources
- the default rule that those same ordinary DB-backed resources are
  implemented through SQLAlchemy ORM models and relationships
- route discovery
- API-backed dynamic data delivery and read-model obligations
- SAFRS-native dynamic-data lanes such as `jsonapi_attr` and `jsonapi_rpc`
- query commitments
- backend validation and fallback verification
- the required decision tree:
  - persisted row data => SAFRS resource
  - DB relationship => ORM relationship plus SAFRS relationship URL/include
  - computed resource field => `jsonapi_attr`
  - explicit operation => `jsonapi_rpc`
  - anything else => documented exception such as `JABase`

It does not define product rule intent or UX behavior.

Load next if needed:

- `../../../specs/contracts/backend/README.md`
