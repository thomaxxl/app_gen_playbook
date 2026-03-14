# admin.yaml Frontend Contract

This file defines the executable frontend subset of `admin.yaml`.

The generator and frontend runtime MUST use this file as the source of:

- resource names
- API endpoint mapping
- labels
- field visibility
- field ordering
- reference behavior
- menu order and visibility

This contract is intentionally split into:

- runtime-consumed keys
- generator-time-only keys
- unsupported v1 keys

This contract is also intentionally distinct from the raw normalization input
expected by `safrs-jsonapi-client`.

The playbook emits:

- `resources` keyed by project resource name such as `Collection`
- `attributes` as a mapping keyed by field name

The current `safrs-jsonapi-client` normalizer expects a different shape. The
frontend runtime MUST adapt this playbook contract before calling
`normalizeAdminYaml(...)`. The playbook MUST NOT change this raw authoring
format only to match a transient client-internal shape.

## Top-level structure

```yaml
resources:
  ResourceName:
    endpoint: /api/resource_path
    label: Resource Label
    user_key: display_field
    menu_order: 10
    hidden: false
    attributes:
      field_name:
        type: text
        label: Field Label
        required: true
        readonly: false
        hidden: false
        list: true
        show: true
        create: true
        edit: true
        order: 10
        widget: text
        placeholder: Enter a value
        help: Help text
      status_id:
        type: reference
        reference: Status
        required: true
        list: true
        show: true
        create: true
        edit: true
      hero_image:
        type: image
        label: Hero Image
        upload_target: hero_image_file_id
        purpose: hero-image
        accept: image/*
        create: true
        edit: true
    tab_groups:
      related:
        label: Related
        relationships:
          - items
```

## Required resource keys

- `endpoint`
  Explicit API path used by the frontend. This resolves the resource-name
  versus API-path ambiguity.
- `label`
  Human-readable resource label.
- `user_key`
  Field to display when a related record needs a readable label.
- `attributes`
  Field contract.

## Supported resource keys

- `menu_order`
  Integer sort for sidebar resources. Consumed by the starter runtime.
- `hidden`
  Hide the resource from generated menu/resource registration. Consumed by the
  starter runtime.
- `tab_groups`
  Relationship group definitions for show/detail pages.
  Generator-time-only in the starter playbook. Not consumed by the shipped v1
  runtime.

## Supported attribute keys

- `type`
  One of `text`, `number`, `boolean`, `datetime`, `reference`, `file`,
  `image`
- `label`
- `required`
- `readonly`
- `hidden`
- `list`
- `show`
- `create`
- `edit`
- `order`
- `reference`
  Required when `type: reference`
- `search`
  Boolean. Marks this field as part of the generated list-search contract.
- `upload_target`
  Required when `type: file` or `type: image`. This is the persisted
  SAFRS scalar or relationship-driving field that receives the stable file id.
- `purpose`
  Optional upload-purpose hint passed to the upload subsystem.
- `accept`
  Optional browser-side accept hint for file/image input widgets.

Upload-backed persistence SHOULD still be represented through normal file-id
fields or relationships. The generator MUST NOT define a raw binary attribute
as a normal SAFRS scalar field in `admin.yaml`.

## Runtime-consumed attribute keys

The shipped starter runtime consumes these keys directly:

- `type`
- `label`
- `required`
- `readonly`
- `hidden`
- `list`
- `show`
- `create`
- `edit`
- `order`
- `reference`
- `search`
- `upload_target`
- `purpose`
- `accept`

## Generator-time-only attribute keys

These keys may still be useful in project-specific generators or future
runtime expansions, but they are not consumed by the shipped v1 runtime:

- `widget`
- `placeholder`
- `help`

## Unsupported v1 assumptions

The shipped starter runtime does not implement these behaviors:

- relationship tabs or grouped show-page sections from `tab_groups`
- per-field widget selection beyond the built-in type mapping
- per-field help/placeholder rendering as a first-class contract
- multi-file upload widgets from one generated field

## Visibility rules

- `hidden: true`
  Hide the field everywhere unless an explicit view-specific flag overrides it
- `list`, `show`, `create`, `edit`
  View-specific visibility flags

If a view-specific flag is omitted:

- default to `true` unless `hidden: true`

If a view-specific flag is explicitly `true`, it overrides `hidden: true` for
that specific view.

## Ordering rules

- If `order` is present, sort ascending by `order`
- otherwise preserve YAML declaration order

## Reference rules

For `type: reference`:

- store the scalar foreign-key id in the record
- use the related resource's `user_key` for display
- fetch related labels explicitly for custom pages
- use the explicit `endpoint` mapping from raw `admin.yaml` when search or
  list routing needs the collection URL

If a resource contains multiple reference fields that point to the same target
resource, each field MUST remain distinct by its own attribute key and label.
The generator and runtime MUST NOT collapse those fields into one display slot
just because they share the same `reference` target.

## Upload field rules

For `type: file` or `type: image`:

- `upload_target` MUST be present
- the generated form field is a frontend upload widget, not a persisted SAFRS
  scalar field by itself
- the persisted write path MUST go through the upload-aware data provider
- the starter runtime assumes a single-file field, not a multi-file list
- `list` and `show` views SHOULD only expose the field when the record shape
  provides a stable logical file value or preview/download URL

## Search rules

`search: true` is supported for:

- `text`

The frontend runtime/data provider MUST use all search-enabled fields to build
a grouped SAFRS OR filter.

Numeric and datetime search are out of scope for the starter runtime unless the
project adds an explicit typed search strategy.

## Datetime note

`datetime` is an allowed schema type, but the shipped starter runtime currently
renders it with date-style components.

That means:

- backend datetimes are still stored as backend-native datetime values
- starter seed/example data uses naive UTC-style timestamps
- datetime display is supported in a basic way
- a dedicated time-of-day widget is not part of the starter runtime contract
- no timezone conversion or display policy is part of the starter v1 contract

## Scope note

This is the supported v1 contract for generated frontends.

If a key is not listed here, the generator MUST NOT guess its meaning.
