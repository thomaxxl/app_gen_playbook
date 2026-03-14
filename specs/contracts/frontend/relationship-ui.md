# Relationship UI Contract

This file defines the required frontend behavior for foreign keys and
relationships.

The generated app MUST implement relationships the same way the Northwind
reference frontend does:

- generated list and show pages MUST display readable related-record labels,
  not raw foreign-key ids
- clicking a related label in a list or summary view MUST open a dialog with a
  related-record summary
- show pages MUST render relationship tabs from relationship metadata
- forms MUST still write scalar foreign-key ids through standard
  `ReferenceInput` controls

Relationship tabs and related-record popups are the default generated
frontend behavior. A generated app MUST implement them unless the current run
explicitly records a different UX decision in its run-owned artifacts.

The runtime MUST remain functional even when normalized relationship metadata
is partial. It MUST combine:

- normalized schema relationship metadata
- `schema.fkToRelationship`
- raw `admin.yaml`

instead of assuming the normalizer output is complete.

## High-level design

The relationship UI MUST be implemented in two layers:

1. metadata construction in `templates/app/frontend/shared-runtime/admin/resourceMetadata.ts.md`
2. UI rendering in:
   - `templates/app/frontend/shared-runtime/resourceRegistry.tsx.md`
   - `templates/app/frontend/shared-runtime/relationshipUi.tsx.md`

The generated frontend MUST NOT treat normalized SAFRS schema as the only
source of truth for relationships. Sparse apps often have incomplete
normalized relationship metadata, so the runtime MUST combine all available
sources and then render from the synthesized relationship model.

## Metadata prerequisites

The shared runtime MUST expose relationship metadata in `ResourceMeta`.

At minimum, `ResourceRelationshipMeta` MUST include:

- `name`
- `label`
- `direction`
- `targetResource`
- `fks`
- `attributes`
- `compositeDelimiter`
- `hidden`
- `hideList`
- `hideShow`
- `hideEdit`

The runtime MUST derive that metadata from:

- normalized SAFRS relationship metadata
- foreign-key mapping such as `schema.fkToRelationship`
- raw `admin.yaml tab_groups`

`admin.yaml tab_groups` MUST be preserved through the adapter layer and used
as authoritative relationship ordering and input even when normalized
relationship metadata is incomplete.

The runtime MUST also be able to look up a relationship by name so that:

- a foreign-key attribute can be replaced by one rendered relationship column
- show-page tabs can be rendered in the author-defined order

`ResourceMeta` MUST also expose:

- `relationshipByName`

and `ResourceAttributeMeta` SHOULD expose:

- `relationship?: ResourceRelationshipMeta`

for any scalar FK attribute that maps to a readable `toone` relationship.

This is the required mechanism for collapsing raw FK columns such as
`device_id` into one readable relationship display item in list/show views.

## Incomplete metadata fallback rules

If normalized schema metadata does not fully define a relationship, the
runtime MUST apply these fallbacks:

1. explicit normalized direction wins
2. explicit normalized values such as `many` or `to-many` => `tomany`
3. explicit normalized values such as `one` or `to-one` => `toone`
4. otherwise plural relationship name => `tomany`
5. otherwise relationship names ending in `_records` => `tomany`
6. otherwise singular relationship name => `toone`
7. if target resource metadata is absent, infer the target resource from
   resource-name matching
8. for inferred `toone`, use `<singular_relationship_name>_id` when that
   attribute exists
9. for inferred `tomany`, inspect the target resource for a `toone`
   relationship back to the parent and use that relationship's foreign-key
   attributes as the reverse join

If fallback inference still cannot establish a safe relationship definition,
the runtime MUST fail visibly rather than silently showing raw ids or empty
tabs as if the contract were complete.

## Minimal sparse example

The runtime MUST be able to handle the sparse example defined in:

- [relationship-sparse-example.md](relationship-sparse-example.md)

## Canonical write shape

For every `toone` relationship:

- the canonical persisted form value MUST remain the scalar foreign-key field
- the runtime MUST NOT replace that write value with an embedded object
- generated forms MUST use `ReferenceInput` / `AutocompleteInput` against the
  foreign-key field

This contract exists so generated CRUD remains compatible with SAFRS JSON:API
writes.

## Optional embedded read shape

For display, a fetched record MAY also contain an embedded related object at:

- `record[relationship.name]`
- `record["rel_" + relationship.name]`

If either embedded object is present, the runtime SHOULD use it as the first
display source before issuing an extra fetch.

The runtime MUST treat those embedded objects as read-only display data.

## Readable label resolution

For a visible related-record label, the runtime MUST resolve in this order:

1. embedded related object `targetMeta.userKey`
2. embedded related object `name`
3. embedded related object `id`
4. local foreign-key scalar value(s)
5. `"-"` when no usable value exists

If the relationship uses composite keys, the runtime MUST join the foreign-key
parts with the schema delimiter or the relationship-specific composite
delimiter.

## List and summary rendering

For generated list and summary/show layouts:

- a `toone` foreign-key-backed attribute MUST render as one relationship
  display item, not as both a foreign-key column and a duplicate relationship
  column
- the visible column label MUST come from the relationship label, not the raw
  foreign-key attribute name
- the visible value MUST use the readable label resolution rules above

The runtime MUST NOT leave a raw scalar such as `customer_id` or `employee_id`
visible in the default generated UI when the relationship metadata is
available.

The generated runtime SHOULD use an explicit display-item model, for example:

- attribute display items
- relationship display items

so that list/show rendering can:

- preserve normal scalar attributes
- replace FK-backed scalar attributes with one relationship display item
- suppress duplicate relationship columns
- honor relationship-level hide flags

This display-item step belongs in `resourceRegistry.tsx`, not in ad hoc
per-page code.

## Related-record dialog behavior

Clickable related labels MUST use a dialog interaction with this behavior:

- clicking the label MUST prevent the parent row click from firing
- the dialog MUST lazy-load the related record when no embedded object is
  already present
- the dialog MUST show loading, error, and empty states
- the dialog MUST show a summary grid of the related record using the target
  resource metadata
- the dialog MUST include `EDIT` and `VIEW` actions for the related record

The dialog SHOULD use the same metadata-driven summary rendering as the target
show view so the display remains consistent.

## Show-page relationship tabs

Generated show pages MUST render relationship tabs from relationship metadata.

Required behavior:

- `tomany` relationships MUST render as related-record datagrids
- `toone` relationships MUST render as summary tabs
- tab visibility MUST honor relationship-level hide flags
- list row actions inside `tomany` tabs MUST keep the icon-only edit/delete
  pattern

For `tomany` tabs:

- the runtime MUST remove obvious back-reference columns that merely restate
  the parent relationship
- the related list SHOULD sort by the target resource `user_key` when present
- if the relationship has no direct foreign-key mapping, the runtime MUST
  infer the reverse join from the target resource's `toone` relationship back
  to the parent when that mapping is available

For `toone` tabs:

- the runtime MUST fetch the related record lazily when it is not embedded
- the runtime MUST show a summary panel rather than a one-row grid

Relationship tab ordering MUST use:

1. author-defined `tab_groups` ordering first
2. schema-discovered relationships not already listed appended afterward

## Default tab selection

The default selected relationship tab MUST prefer the most useful
relationship, not simply the first declared relationship.

The starter priority MUST be:

1. `tomany` relationships targeting a different resource
2. `toone` relationships targeting a different resource
3. `tomany` self-references
4. `toone` self-references

This rule avoids landing first on empty self-reference tabs such as recursive
parent/child links when a more useful detail list exists.

## Custom views

If a custom page surfaces relationships, it SHOULD reuse the same label
resolution and summary behavior as the generated runtime.

At minimum, a custom page MUST NOT show raw foreign-key ids when the same
screen could reasonably show the related resource `user_key`.

## Validation requirements

The frontend validation suite MUST prove at least one end-to-end example of:

- a readable related label in a generated list
- opening the related-record dialog from that list
- the dialog showing `EDIT` and `VIEW`
- a generated show page with both `toone` and `tomany` relationship tabs
- a sparse-schema relationship example where `tab_groups` plus fallback
  inference still produce a working `tomany` tab

If a run explicitly disables or replaces relationship tabs or related-record
popups, that exception MUST be documented in the run-owned UX artifacts before
delivery. Silence or omission is not an override.
