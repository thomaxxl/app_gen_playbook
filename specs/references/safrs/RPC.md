# RPC and `jsonapi_rpc`

Use this note when the need is an explicit action, operation, or service-like
call rather than an ordinary persisted resource read.

Required takeaway:

- `@jsonapi_rpc` is the default SAFRS lane for explicit backend operations
- use it before inventing an unrelated custom `/api/ops/` endpoint for a
  resource-owned action
- RPC is for explicit operations, not for avoiding normal resource or
  relationship exposure

Local references:

- `../../../../demo/examples/mini_examples/ex08_rpc.py`
- `../../../specs/contracts/backend/data-sourcing.md`
