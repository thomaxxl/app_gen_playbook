# Resource Classification

## Resource classification table

| Resource | Class | CRUD expectation | Reference-only | Appears in menu | Requires custom-page logic | Singleton or first-class | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Service` | core CRUD | full CRUD | no | yes | dashboard consumes it | first-class | parent aggregate |
| `ConfigurationItem` | core CRUD | full CRUD | no | yes | dashboard and relationship UI rely on it | first-class | workflow-heavy operational record |
| `OperationalStatus` | reference or status | limited CRUD | no | yes | no | first-class | lookup and copied-field rule source |

## Singleton versus first-class decisions

- `Service` remains first-class because users manage multiple service rows.
- `OperationalStatus` remains a first-class reference resource because the
  app exposes and validates status definitions instead of hardcoding them.

## Deferred or excluded resources

- no separate `User` or `Team` resource in the preserved example
- no dashboard-only aggregate resource is modeled as a standalone API resource
