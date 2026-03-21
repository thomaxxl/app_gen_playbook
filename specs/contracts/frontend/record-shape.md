# Client Record Shape

This file defines the normalized record shape expected by the generated
frontend.

## Stable rules

- The primary key MUST be normalized to `id`
- All other attribute keys MUST preserve the exact backend/admin.yaml field names
- The runtime MUST NOT perform automatic case conversion
- Reference fields MUST remain scalar ids in the normalized record as the
  canonical write shape
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
- generated relationship rendering MUST remain functional even when embedded
  related objects are absent and normalized relationship metadata is partial
- custom pages MUST prefer embedded related objects from `include=...`, then
  canonical relationship routes, then id-based fallback fetches or the shared
  relationship helper when they need readable labels
- custom pages MUST NOT assume only one embedded-object field name unless they
  control the producer; the shared runtime supports both `relationshipName`
  and `rel_<relationshipName>`

## Display rule for references

When displaying a related record in a custom view:

1. prefer an embedded related object when one is present
2. otherwise use canonical relationship metadata and the parent relationship
   route when available
3. otherwise read the local scalar id field such as `status_id`
4. fetch the related resource by id as a fallback
5. display the related resource's `user_key` field or `label`

If normalized schema relationship metadata is incomplete, custom pages SHOULD
reuse the shared relationship helper instead of inventing their own fallback
logic.

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
