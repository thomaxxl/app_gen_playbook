# Models And Naming Contract

This file defines the backend model contract and the naming boundaries the
playbook is allowed to specify locally.

## Model base contract

Each exposed model MUST inherit from:

- `SAFRSBase`
- the local SQLAlchemy `Base`

Pattern:

```python
class Collection(SAFRSBase, Base):
    __tablename__ = "collections"
```

## ORM default rule

For persisted database-backed tables and relationships that are appropriate for
normal resource delivery, the backend MUST use mapped SQLAlchemy ORM models and
relationships as the default implementation lane.

The backend MUST NOT treat ad hoc row dictionaries, manual SQL result
translation, or raw-SQL-only handlers as the normal implementation for such
resources unless the run-owned architecture and backend-design artifacts record
an explicit exception.

## Naming policy the playbook does own

- Python class names: `PascalCase`
- SQL table names: project-defined `snake_case`
- ORM column names: `snake_case`
- ORM relationship names: explicit and project-defined
- `admin.yaml` resource keys: explicit and project-defined
- `admin.yaml` relationship names: explicit and must match the ORM/SAFRS
  relationship contract

## Naming policy the playbook does not infer

The playbook MUST NOT claim that it can infer SAFRS wire naming from table
names alone.

The implementation MUST treat these as runtime facts that require validation:

- actual SAFRS collection route paths
- actual JSON:API wire `type` values
- mutation payload `type` values

The generated backend and tests must discover those values from the running app
through `admin.yaml`, generated docs, or live responses.

## Starter example, not mandatory domain shape

The starter worked example uses:

- `Collection`
- `Item`
- `Status`

This is a house-style example, not a mandatory domain for every app effort.
Non-starter apps SHOULD document their deviation in:

- `../architecture/domain-adaptation.md`

## Starter example fields

`Collection`

- `id: Integer` primary key
- `name: String` unique, non-null
- `item_count: Integer` derived, non-null, default `0`
- `total_estimate_hours: Float` derived, non-null, default `0`

`Item`

- `id: Integer` primary key
- `title: String` non-null
- `estimate_hours: Float` non-null
- `completed_at: DateTime | None`
- `collection_id: Integer` foreign key, non-null
- `status_id: Integer` foreign key, non-null
- `status_code: String` derived, non-null, default `""`
- `is_completed: Boolean` derived, non-null, default `False`

`Status`

- `id: Integer` primary key
- `code: String` unique, non-null
- `label: String` non-null
- `is_closed: Boolean` non-null, default `False`

## Starter relationship example

- `Collection.items`
  one-to-many, `passive_deletes=True`, no ORM delete-orphan cascade
- `Item.collection`
  many-to-one, required
- `Item.status`
  many-to-one, required
- `Status.items`
  one-to-many, no delete cascade to `Item`

## Multiple-reference adaptation rule

For non-starter domains, a model MAY reference the same target resource more
than once.

In that case:

- each ORM foreign-key column MUST have a distinct semantic name
- each ORM relationship MUST have a distinct semantic name
- the `admin.yaml` field names and labels MUST preserve that distinction

Worked example:

- `Pairing.white_player_id -> Player`
- `Pairing.black_player_id -> Player`
- `Pairing.white_player`
- `Pairing.black_player`

See `../../architecture/nonstarter-worked-example.md`.

## Delete/nullability policy

- an `Item` cannot exist without a `Collection`
- an `Item` cannot exist without a `Status`
- deleting a `Collection` deletes its `Item` rows through database-enforced
  foreign-key cascade, not ORM-side delete recursion
- deleting a `Status` while referenced by an `Item` is not allowed
- migrations are out of scope for the starter playbook; use `create_all()` only
- the implementation MUST enable SQLite foreign-key enforcement so the
  database-level delete contract actually executes

## Rule-facing derived columns

The starter rules rely on these persisted derived columns:

- `Collection.item_count`
- `Collection.total_estimate_hours`
- `Item.status_code`
- `Item.is_completed`

The implementation MUST treat them as backend-managed read-only fields.

## Exposed models contract

The backend MUST define:

```python
EXPOSED_MODELS = (Collection, Item, Status)
```

That tuple is the source of truth for `api.expose_object(...)` in the starter
example.

For non-starter runs, the same rule applies: resources marked as SAFRS-exposed
must be represented by real mapped ORM classes in `EXPOSED_MODELS`, not only
by custom route handlers.
