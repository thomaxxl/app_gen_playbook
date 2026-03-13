# `frontend/src/generated/resources/Status.tsx`

See also:

- [../../../../../specs/contracts/frontend/runtime-contract.md](../../../../../specs/contracts/frontend/runtime-contract.md)
- [../../../reference/admin.yaml.md](../../../reference/admin.yaml.md)

This file is the explicit wrapper for the `Status` resource.

```tsx
import { makeSchemaDrivenPages } from "../../shared-runtime/resourceRegistry";

export const StatusPages = makeSchemaDrivenPages("Status");
```

Notes:

- Keep one file per resource, even when the internals stay schema-driven.
- Resource names must match the backend and `admin.yaml` exactly.
- The registry wiring belongs in `resourcePages.ts.md`.
