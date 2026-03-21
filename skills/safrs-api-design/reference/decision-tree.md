# SAFRS API Design Decision Tree

Start with the actual data need, not an endpoint name.

## 1. Is it persisted DB row data?

If yes:

- create or reuse a real SQLAlchemy model
- expose it through SAFRS
- verify live resource discovery in `/jsonapi.json`

## 2. Is it a relationship between exposed resources?

If yes:

- define a real ORM relationship
- use the SAFRS relationship endpoint as the canonical read surface
- document the exact relationship name
- use `include=...` when the caller wants related data embedded with the parent resource

Typical good patterns:

- `/Users/{id}/books`
- `include=books`
- `include=books.author`

Typical bad patterns:

- `/api/user_books_lookup`
- `/api/book_author_summary`

## 3. Is it derived data that belongs on the resource representation?

If yes:

- use `@jsonapi_attr`
- keep the field on the resource
- remember that filtering and sorting are not automatic for `@jsonapi_attr`

## 4. Is it an explicit operation?

If yes:

- use `@jsonapi_rpc`
- prefer class-level RPC on the collection for collection-wide actions
- prefer instance-level RPC on the instance path for object-scoped actions

## 5. Is it truly not resource-shaped?

Only then consider:

- JABase / stateless endpoint
- custom read-model endpoint
- custom ops endpoint

This requires a written exception.

## Review questions before approving a custom endpoint

Answer every question explicitly.

- Why is this not a real resource?
- Why is this not a relationship under the owning resource?
- Why is `include=...` not enough?
- Why is this not a computed field via `@jsonapi_attr`?
- Why is this not an operation via `@jsonapi_rpc`?
- What is the replacement contract?
- What live evidence proves the surrounding SAFRS surface still exists where appropriate?

## Hiding or restricting relationships

When a relationship exists but should not be public:

- use SAFRS visibility controls
- document the choice in the relationship map
- do not omit the relationship and rebuild it with a side endpoint

## Frontend rule of thumb

For relational reads, prefer in this order:

1. `include=...`
2. relationship endpoint
3. fallback fetch by related id only when needed

Scalar foreign keys may remain a write convenience.
They are not the canonical read-side API for relationships.
