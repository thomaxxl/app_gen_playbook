# Package Compatibility Contract

## Record shape that wrappers must preserve

A package-compatible normalized record must preserve:

- `id`
- `ja_type`
- `attributes`
- `relationships`
- flattened attributes at top level
- optional embedded related data at:
  - `record[relationshipName]`
  - `record["rel_" + relationshipName]`

This allows shared relationship UI to:
- display embedded related labels immediately
- inspect original relationship linkage
- fall back cleanly when embedded data is absent
- stay aligned with the adapter's own normalization behavior

## Collection / detail normalization

For list, get-one, get-many, and many-reference flows:
- included resources must remain available to normalization / hydration
- to-one autoload behavior must remain compatible with the package schema
- to-many inclusion must not be silently discarded when the adapter asked for it

A local wrapper that turns a JSON:API document into only:

```ts
{ id, ...attributes }
```

is not compatible.

## Schema expectations

The package schema model includes richer relationship metadata than the playbook's lightweight runtime should try to reinvent. At minimum, frontend runtime code must preserve or remain mappable to:

- `resourceByType`
- `relationshipsByName`
- `fkToRelationship`
- relationship direction
- target resource
- FK list
- autoload controls
- composite delimiter controls

If the playbook authoring contract needs an adapter, adapt into this schema model. Do not maintain a second, weaker schema model forever.

## `tab_groups`

`tab_groups` is not optional decoration.

It is the authoring surface for:
- which relationships appear in tabs
- their order
- their labels
- relationship-level visibility

If the package raw-input shape differs from the playbook authoring contract, the adapter must carry `tab_groups` forward so the package schema and the shared relationship UI can still agree on relationship meaning.

## Search-wrapper compatibility

If a `q` search wrapper exists, it must prove:

- `include=...` survives search requests
- normalized search results preserve package record shape
- relationship UI works on searched list results the same way it works on ordinary list results
- total extraction stays compatible with JSON:API meta handling

## RPC / service-call compatibility

Custom SAFRS methods and raw JSON service calls should ride on the package provider's `execute()` so they inherit:
- auth header hooks
- abort handling
- JSON:API error mapping
- consistent normalization for JSON:API responses
