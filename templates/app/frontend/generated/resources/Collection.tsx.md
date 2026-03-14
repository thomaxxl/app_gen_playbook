# `frontend/src/generated/resources/Collection.tsx`

See also:

- [../../../../../specs/contracts/frontend/runtime-contract.md](../../../../../specs/contracts/frontend/runtime-contract.md)
- [../../../reference/admin.yaml.md](../../../reference/admin.yaml.md)

This file is the explicit wrapper for the `Collection` resource.

STARTER-ONLY WARNING:

- this file is a starter example
- `rename-only` and `non-starter` runs MUST replace it with the actual
  resource wrapper declared by the run-owned naming artifacts

```tsx
import { makeSchemaDrivenPages } from "../../shared-runtime/resourceRegistry";

export const CollectionPages = makeSchemaDrivenPages("Collection");
```

Notes:

- Keep one file per resource, even when the internals stay schema-driven.
- Resource names must match the backend and `admin.yaml` exactly.
- The registry wiring belongs in `resourcePages.ts.md`.
