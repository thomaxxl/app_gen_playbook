# Instances without a SQLAlchemy model

Use this note only when the normal SAFRS resource, relationship, include,
`jsonapi_attr`, and `jsonapi_rpc` lanes were evaluated first and found
insufficient.

Required takeaway:

- `JABase` or stateless SAFRS endpoints are an exception lane
- they are not the default answer for DB-backed rows or relationships
- using `JABase` requires an explicit architecture exception with a replacement
  contract

Use this lane only when the need is truly not best modeled as:

- a SAFRS resource
- a SAFRS relationship
- `include=...`
- `@jsonapi_attr`
- `@jsonapi_rpc`

Local references:

- `../../../../demo/vendor/safrs/safrs/jabase.py`
- `../../../specs/contracts/backend/data-sourcing.md`
