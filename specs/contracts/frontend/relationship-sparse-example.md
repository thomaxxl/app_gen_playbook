# Sparse Relationship Example

This file defines the minimum sparse-schema relationship example that the
generated frontend runtime MUST be able to handle.

Use this file when:

- normalized relationship metadata is partial
- database foreign-key constraints are absent or not introspectable
- `admin.yaml tab_groups` must drive relationship UI even when the normalizer
  output is incomplete

## Minimal example

Resources:

- `Device`
- `Session`

Minimal assumptions:

- `Device` has a tab group that lists `sessions`
- `Session` has an attribute `device_id`
- normalized schema does not fully declare relationship direction
- normalized schema may omit the target resource for `sessions`
- database foreign-key constraints are not available for runtime introspection

## Required runtime outcome

The frontend runtime MUST still be able to:

1. render a `Sessions` relationship tab on the `Device` show page
2. infer that `sessions` is `tomany`
3. infer that the target resource is `Session`
4. infer that `Session.device_id` is the reverse join key
5. load related `Session` rows for the selected `Device`

## Generalized fallback rules

When normalized relationship metadata is incomplete, the runtime MUST apply
these fallbacks in order:

1. use normalized schema relationship metadata when present
2. use `schema.fkToRelationship` when available
3. use raw `admin.yaml tab_groups` as authoritative relationship input and
   ordering
4. infer direction from relationship naming:
   - plural name => `tomany`
   - singular name => `toone`
5. infer target resource from resource-name matching when target metadata is
   absent
6. for inferred `toone`, infer the foreign-key attribute as
   `<singular_relationship_name>_id` when present
7. for inferred `tomany`, inspect the target resource for a `toone`
   relationship back to the parent and use that relationship's foreign-key
   attributes as the reverse join

If no fallback path can establish a safe relationship contract, the runtime
MUST fail visibly instead of silently rendering a broken raw-id UI.
