# Resource Naming

## Resource naming table

| Resource | Model class | SQL table | admin.yaml key | Intended relationship names | Provisional endpoint | Discovered endpoint | Discovered wire type | Validation status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Service` | `Service` | `services` | `Service` | `items` | `/api/services` | `/api/services` | `Service` | validated in preserved example |
| `ConfigurationItem` | `ConfigurationItem` | `configuration_items` | `ConfigurationItem` | `service`, `status` | `/api/configuration_items` | `/api/configuration_items` | `ConfigurationItem` | validated in preserved example |
| `OperationalStatus` | `OperationalStatus` | `operational_statuses` | `OperationalStatus` | `items` | `/api/operational_statuses` | `/api/operational_statuses` | `OperationalStatus` | validated in preserved example |

## Relationship naming notes

- `ConfigurationItem` references both `Service` and `OperationalStatus`
  directly through scalar FK fields.
- `Service` exposes a list relationship to `ConfigurationItem` through
  `items`.
- `OperationalStatus` exposes a list relationship to `ConfigurationItem`
  through `items`.

## Runtime validation notes

This preserved example has already been validated against the generated app
shape. Fresh runs MUST still perform their own route and wire-type validation.

## Non-starter exceptions

The example is intentionally non-starter. Relationship metadata therefore
depends on explicit `admin.yaml` and fallback inference rather than starter
resource assumptions.
