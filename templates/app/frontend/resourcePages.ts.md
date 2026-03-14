# `frontend/src/generated/resourcePages.ts`

See also:

- [../../../specs/contracts/frontend/runtime-contract.md](../../../specs/contracts/frontend/runtime-contract.md)

This file is the explicit resource registry consumed by `SchemaDrivenAdminApp`.

The starter names below are examples only. For a real app, replace them with
the wrappers declared by
`../../../runs/current/artifacts/architecture/resource-naming.md`.

STARTER-ONLY WARNING:

- keeping the starter trio here in a `rename-only` or `non-starter` run is a
  contract error

```tsx
import type { ResourcePages } from "../shared-runtime/resourceRegistry";
import { CollectionPages } from "./resources/Collection";
import { ItemPages } from "./resources/Item";
import { StatusPages } from "./resources/Status";

export const resourcePages: ResourcePages[] = [
  CollectionPages,
  ItemPages,
  StatusPages,
];
```

Notes:

- This is not optional.
- The app must import this file and pass it into `SchemaDrivenAdminApp`.
- Non-starter domains MUST replace the starter trio with the actual app
  resource wrapper set.
