# Client Record Shape

This file defines the normalized record shape expected by the generated
frontend.

## Stable rules

- The primary key MUST be normalized to `id`
- All other attribute keys MUST preserve the exact backend/admin.yaml field names
- The runtime MUST NOT perform automatic case conversion
- Reference fields MUST remain scalar ids in the normalized record
- Read-only embedded related objects MAY also be present at
  `record[relationshipName]` or `record["rel_" + relationshipName]`
- Embedded related objects MUST be treated as optional display aids, not as the
  canonical persisted write shape
- At the app layer, `id` MUST be treated as opaque. The implementation MUST NOT
  rely on numeric identity semantics.

## Example

For an `Item` resource:

```json
{
  "id": "42",
  "title": "Board passengers",
  "estimate_hours": 2.5,
  "completed_at": null,
  "status_code": "scheduled",
  "is_completed": false,
  "status_id": 2,
  "collection_id": 1,
  "status": {
    "id": "2",
    "code": "done",
    "label": "Done"
  }
}
```

Related resources are still separate records for canonical fetch/write flows:

```json
{
  "id": "2",
  "code": "done",
  "label": "Done"
}
```

## Consequences

- generated list/show/edit pages MAY read scalar fields directly
- generated list/show pages MAY also use optional embedded related objects for
  display when available
- custom pages MUST fetch related resources explicitly or reuse the shared
  relationship helper when they need readable labels
- custom pages MUST NOT assume only one embedded-object field name unless they
  control the producer; the shared runtime supports both `relationshipName`
  and `rel_<relationshipName>`

## Display rule for references

When displaying a related record in a custom view:

1. prefer an embedded related object when one is present
2. otherwise read the local scalar id field such as `status_id`
3. fetch the related resource by id
4. display the related resource's `user_key` field or `label`

This is why `admin.yaml` must define both:

- `endpoint`
- `user_key`

## File-value note

If the app includes upload-backed fields, the persisted record shape MUST still
carry only stable backend values such as:

- `hero_image_file_id`
- attachment resource ids
- logical media URLs inside fetched `StoredFile` metadata resources

Temporary browser-only values containing `rawFile` are form-state artifacts,
not persisted record fields.
