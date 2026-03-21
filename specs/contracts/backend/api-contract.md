# Backend Integration Contract

This file defines the project-specific SAFRS integration contract for the
generated backend.

It does not redefine generic JSON:API semantics. Those are delegated to
JSON:API and SAFRS itself.

## Stable integration points

The generated app relies on these SAFRS/backend behaviors staying stable:

- canonical resource names
- canonical relationship names
- canonical schema URL `/jsonapi.json`
- ordinary persisted resource delivery coming from real ORM-backed SAFRS
  resources, not hand-built JSON stand-ins
- ordinary persisted relationship delivery coming from real ORM-backed SAFRS
  relationship URLs and include paths, not custom summary endpoints
- `/jsonapi.json` representing real SAFRS-backed resource discovery, not only
  a renamed FastAPI OpenAPI document
- include support for declared relationship names
- SAFRS query behavior described in `query-contract.md`
- JSON:API error normalization visible to the frontend
- runtime-discovered collection paths and wire `type` values remaining aligned
  with the frontend/provider configuration

## Identifier rule

- JSON:API `id` is the canonical wire identifier
- JSON:API `id` is serialized as a string on the wire
- database primary keys may still be integer columns internally

## Relationship read and write rule

The starter app MAY keep scalar foreign-key columns such as `collection_id`
and `status_id` as a write convenience.

That does not change the canonical read contract:

- canonical read, drill-down, and related-record inspection for DB
  relationships come from SAFRS relationship URLs and/or `include=...`
- a scalar FK attribute is not permission to invent a side endpoint that
  re-exports related DB information outside the owning resource's SAFRS
  surface
- if a relationship is intentionally not public, the run-owned design must
  record that as an explicit SAFRS decision and replacement contract

## Runtime discovery rule

The implementation MUST NOT infer JSON:API wire `type` values or collection
paths from SQL table names alone.

Instead, the implementation MUST:

- discover collection paths from actual SAFRS output and copy them into
  `admin.yaml`
- discover wire `type` values from live list or single-record responses
- use those discovered `type` values in mutation payload tests

## Contract notes

- attribute keys MUST be snake_case unless the project explicitly documents a
  different rule
- relationship names are explicit backend/application decisions and MUST match
  `admin.yaml`
- `admin.yaml` resource keys remain project-defined and map to the explicit
  `endpoint` field
- persisted derived rule fields may appear in `attributes` and should be
  treated as read-only by clients
- starter error responses are only required to expose a readable top-level
  message such as `errors[].title` and `errors[].detail`
- field-pointer semantics are out of scope for the starter contract unless the
  project adds them explicitly

## File-metadata extension

If the app supports uploaded files, the backend MAY expose file metadata
resources such as `StoredFile`, `FileVariant`, and `FileAttachment` through
SAFRS.

In that case:

- file metadata resources MUST behave like normal SAFRS JSON:API resources
- binary upload bodies MUST still go through dedicated multipart endpoints
- frontend-visible file attributes MUST expose logical URLs such as
  `/media/{file_id}`, not raw storage paths
