# `frontend/src/App.tsx`

See also:

- [../../../specs/contracts/frontend/runtime-contract.md](../../../specs/contracts/frontend/runtime-contract.md)
- [../../../specs/contracts/frontend/custom-views.md](../../../specs/contracts/frontend/custom-views.md)

Keep the app root thin, but make resource wiring explicit.

```tsx
import { CustomRoutes } from "react-admin";
import { Navigate, Route } from "react-router-dom";

import Landing from "./Landing";
import { appConfig } from "./config";
import { resourcePages } from "./generated/resourcePages";
import { SchemaDrivenAdminApp } from "./shared-runtime/SchemaDrivenAdminApp";

export default function App() {
  return (
    <SchemaDrivenAdminApp
      appConfig={appConfig}
      resourcePages={resourcePages}
    >
      <CustomRoutes noLayout>
        <Route element={<Navigate replace to="/Landing" />} path="/" />
        <Route element={<Landing />} path="/Landing" />
      </CustomRoutes>
    </SchemaDrivenAdminApp>
  );
}
```

Notes:

- Do not bury project-specific API paths in the component tree.
- Keep app title and endpoint config in `config.ts`.
- `Landing.tsx` is part of the starter app, not an optional afterthought.
- `children` inside `SchemaDrivenAdminApp` is the official custom-route
  extension point.
