# Bootstrap And Database Lifecycle

This file defines SQLite lifecycle and seed behavior for the starter backend in
this playbook.

## Database scope

The starter backend uses:

- SQLite
- `create_all()`
- no migration system

Migrations and schema evolution are intentionally out of scope for this spec.

## Startup DB behavior

- The backend creates the SQLite file if it does not exist
- The backend runs `Base.metadata.create_all(engine)` on startup
- Startup must not drop or recreate populated tables

## Foreign key behavior

SQLite foreign key enforcement must be enabled.

Do not rely on SQLite's default behavior.

The starter delete contract MUST prefer database-enforced `ON DELETE`
behavior plus passive ORM relationships over ORM-side delete-orphan cascade on
LogicBank-managed child collections.

## Bootstrap behavior

Bootstrap must be:

- idempotent
- safe to call on every startup
- non-destructive for existing data

## Empty-DB detection

Use a stable root-table check such as:

- `session.query(Status).count() == 0`

Do not rely on temporary tables or partial row existence checks.

This is intentionally a starter simplification, not a repair strategy for
partially corrupted or partially seeded databases. A real production bootstrap
strategy would need explicit repair or migration logic instead of only this
seed gate.

## Required bootstrap order

The canonical startup order is defined in:

- `runtime-and-startup.md`

Within that canonical order, bootstrap-specific work MUST follow this
sequence:

1. validate `admin.yaml` static contract shape
2. open a managed session
3. detect whether the DB is empty
4. insert reference rows only if empty
5. commit and let activated LogicBank rules populate derived columns

This file MUST NOT be read as an independent alternative startup-order source.

## Seed rules

- seed data must not duplicate on repeat startup
- seed data should cover at least one resource relationship path
- seed data should support later tests that exercise both valid and invalid
  rule mutations

## Recommended starter seed

- `3` statuses
- `1` collection
- `2` items

That gives enough data to validate:

- list endpoints
- relationship endpoints
- aggregate rules
- delete behavior
