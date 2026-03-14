# `frontend/src/App.tsx`

See also:

- [../../../specs/contracts/frontend/runtime-contract.md](../../../specs/contracts/frontend/runtime-contract.md)
- [../../../specs/contracts/frontend/home-and-entry.md](../../../specs/contracts/frontend/home-and-entry.md)
- [../../../specs/contracts/frontend/custom-views.md](../../../specs/contracts/frontend/custom-views.md)

Keep the app root thin, but make resource wiring explicit.

```tsx
import HomeIcon from "@mui/icons-material/Home";
import { CustomRoutes, Resource } from "react-admin";
import { Navigate, Route } from "react-router-dom";

import Home from "./Home";
import { appConfig } from "./config";
import { resourcePages } from "./generated/resourcePages";
import { SchemaDrivenAdminApp } from "./shared-runtime/SchemaDrivenAdminApp";

export default function App() {
  return (
    <SchemaDrivenAdminApp
      appConfig={appConfig}
      resourcePages={resourcePages}
    >
      <>
        <Resource
          icon={HomeIcon}
          list={Home}
          name="Home"
          options={{ label: "Home" }}
        />
        <CustomRoutes noLayout>
          <Route element={<Navigate replace to="/Home" />} path="/" />
        </CustomRoutes>
      </>
    </SchemaDrivenAdminApp>
  );
}
```

Notes:

- Do not bury project-specific API paths in the component tree.
- Keep app title and endpoint config in `config.ts`.
- `Home.tsx` is the required in-admin landing page with sidebar presence.
- The starter redirect to `/Home` is correct unless the run-owned
  `route-and-entry-model.md`, `navigation.md`, and `landing-strategy.md`
  explicitly approve a different primary entry route.
- `Landing.tsx` is starter-only and MUST NOT be imported here unless the
  run-owned custom-view spec explicitly enables it.
- If the app needs a no-layout route, add it explicitly through
  `CustomRoutes noLayout` after the UX artifact set defines it.
- `children` inside `SchemaDrivenAdminApp` is the official custom-route
  extension point.
