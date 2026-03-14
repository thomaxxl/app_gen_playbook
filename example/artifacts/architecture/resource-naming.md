# Resource Naming

## Resource naming table

| Resource | Model class | SQL table | admin.yaml key | Intended relationship names | Provisional endpoint | Discovered endpoint | Discovered wire type | Validation status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Gallery` | `Gallery` | `galleries` | `Gallery` | `ImageAssetList`, `ShareStatusList` | `/api/Gallery` | `/api/Gallery` | `Gallery` | validated in example app |
| `ImageAsset` | `ImageAsset` | `image_assets` | `ImageAsset` | `Gallery`, `ShareStatus` | `/api/ImageAsset` | `/api/ImageAsset` | `ImageAsset` | validated in example app |
| `ShareStatus` | `ShareStatus` | `share_statuses` | `ShareStatus` | `ImageAssetList` | `/api/ShareStatus` | `/api/ShareStatus` | `ShareStatus` | validated in example app |

## Relationship naming notes

- `ImageAsset` references both `Gallery` and `ShareStatus` directly.
- `Gallery` exposes a list relationship to `ImageAsset`.
- `ShareStatus` exposes a list relationship to `ImageAsset` because status is a
  separate managed reference resource.

## Runtime validation notes

This preserved example has already been validated against the running app.
Fresh runs MUST still perform their own route and wire-type validation.

## Non-starter exceptions

None. This example stays within a rename-only starter shape.
