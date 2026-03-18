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
- include support for declared relationship names
- SAFRS query behavior described in `query-contract.md`
- JSON:API error normalization visible to the frontend
- runtime-discovered collection paths and wire `type` values remaining aligned
  with the frontend/provider configuration

## Identifier rule

- JSON:API `id` is the canonical wire identifier
- JSON:API `id` is serialized as a string on the wire
- database primary keys may still be integer columns internally

## SAFRS-specific starter assumption

The starter app intentionally relies on one SAFRS convenience behavior:

- foreign-key columns such as `collection_id` and `status_id` are exposed as
  scalar writable attributes

This is a SAFRS-specific assumption for the starter templates. It is not being
presented as generic JSON:API doctrine.

If a future generator variant wants to stay more relationship-oriented, that
variant must change the client/provider and test templates together.

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
