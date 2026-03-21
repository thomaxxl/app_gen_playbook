# API Functionality

Use this note when deciding whether a need still fits normal SAFRS resource
delivery.

Required takeaway:

- SAFRS already provides normal collection/item/relationship semantics
- filtering, sorting, pagination, and include behavior belong on the SAFRS
  lane first
- a custom endpoint is not justified merely because the frontend wants a
  filtered, sortable, or includable read of DB-backed data

Before approving a custom endpoint, record why the need is not satisfied by:

- the resource endpoint
- the relationship endpoint
- `include=...`
- `@jsonapi_attr`
- `@jsonapi_rpc`
