# Relationship Proof Checklist

Use this when a backend design claims that a DB relationship is exposed through SAFRS.

## Design-time proof

- Resource names are final enough to test
- Exact ORM relationship name is recorded
- Relationship cardinality is recorded
- Nullability and delete behavior are recorded
- `include=...` path is recorded when required
- relationship visibility choice is recorded
- `relationship_item_mode` choice is recorded when relevant

## Live API proof

- resource appears in live `/jsonapi.json`
- relationship path exists live
- relationship item path exists live when enabled
- declared include path works live
- nested include path works live when promised
- hidden relationships are actually hidden when claimed

## Frontend alignment proof

- related-record tab or dialog maps to a real relationship name
- frontend is not forced onto a custom DB lookup endpoint for an ordinary relationship
- scalar FK use, if any, is documented as write-side convenience or fallback, not primary relationship API

## Test proof

- API contract test covers at least one relationship route
- API contract test covers at least one `include=...` request for each required include path
- computed fields introduced with `@jsonapi_attr` are tested
- RPC methods introduced with `@jsonapi_rpc` are tested
- exceptions have dedicated tests for the custom surface and for the surrounding canonical SAFRS surface

## Failure conditions

Fail the design or review if any of these are true:

- the relationship exists only in prose, not in ORM mapping
- the UI depends on a custom summary endpoint for an ordinary DB relationship
- a required include path is documented but does not work live
- the live schema is hand-authored or fake and not backed by SAFRS exposure
- the exception record is missing for a custom endpoint that replaced a normal SAFRS lane
