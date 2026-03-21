# JSON Encoding and `jsonapi_attr`

Use this note when the API needs a computed or derived field that belongs on a
resource representation.

Required takeaway:

- `@jsonapi_attr` is the default SAFRS lane for computed resource attributes
- use it before inventing a custom summary endpoint for a resource-level
  derived value
- a field that is not a physical DB column can still belong on the canonical
  resource representation

Local references:

- `../../../specs/contracts/backend/data-sourcing.md`
- `../../../../projects/northwind/reference/models_guidance.py`
