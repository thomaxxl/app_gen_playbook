# Resource Classification

## Resource classification table

| Resource | Class | CRUD expectation | Reference-only | Appears in menu | Requires custom-page logic | Singleton or first-class | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Gallery` | core CRUD | full CRUD | no | yes | dashboard consumes it | first-class | parent aggregate |
| `ImageAsset` | core CRUD | full CRUD | no | yes | upload/dashboard behavior | first-class | workflow-heavy |
| `ShareStatus` | reference or status | limited CRUD | no | yes | no | first-class | lookup and rule source |

## Singleton versus first-class decisions

- `Gallery` remains first-class because users manage multiple collections.
- `ShareStatus` remains a first-class reference resource because the app
  exposes and validates status definitions rather than hardcoding them.

## Deferred or excluded resources

- no separate `User` or `Organization` resource in the preserved example
- no dashboard-only aggregate resource is modeled as a standalone API resource
