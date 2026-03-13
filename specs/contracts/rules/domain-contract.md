# Rules Domain Contract

This file defines the minimum mapped schema required for the starter rules.

## Required mapped resources

- `Collection`
- `Item`
- `Status`

## Required mapped relationships

- `Collection.items`
  one-to-many
- `Item.collection`
  many-to-one
- `Item.status`
  many-to-one
- `Status.items`
  one-to-many

These names are part of the rule contract. The rules MUST NOT guess
relationship names.

## Required mapped columns

`Collection`:

- `id`
- `name`
- `item_count`
- `total_estimate_hours`

`Item`:

- `id`
- `title`
- `estimate_hours`
- `completed_at`
- `collection_id`
- `status_id`
- `status_code`
- `is_completed`

`Status`:

- `id`
- `code`
- `label`
- `is_closed`

## Derived-column storage contract

These are persisted database columns:

- `Collection.item_count`
- `Collection.total_estimate_hours`
- `Item.status_code`
- `Item.is_completed`

They are not virtual-only attributes in the starter spec.

## Read-only contract

These derived columns are backend-managed and MUST be treated as read-only in
the generated frontend/admin contract:

- `item_count`
- `total_estimate_hours`
- `status_code`
- `is_completed`

## Completed-at semantics

The starter rule is validation-only, not transition-aware.

That means:

- if an item is in the completed state, `completed_at` must be non-null
- the rules do not auto-stamp `completed_at`
- the rules do not auto-clear `completed_at` on reopen

If a project later needs transition-aware behavior, that belongs in a more
advanced formula/event pattern, not in the starter contract.
