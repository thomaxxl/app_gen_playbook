# Backend Contract Summary

Load this when a task touches backend runtime, exposure, startup, or API
verification behavior.

The backend contract controls:

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

It does not define product rule intent or UX behavior.

Load next if needed:

- `../../../specs/contracts/backend/README.md`
