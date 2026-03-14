# `frontend/src/App.tsx`

See also:

- [../../../specs/contracts/frontend/runtime-contract.md](../../../specs/contracts/frontend/runtime-contract.md)
- [../../../specs/contracts/frontend/custom-views.md](../../../specs/contracts/frontend/custom-views.md)

Keep the app root thin, but make resource wiring explicit.

```tsx
import HomeIcon from "@mui/icons-material/Home";
import { CustomRoutes, Resource } from "react-admin";
import { Navigate, Route } from "react-router-dom";

import Home from "./Home";
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
      <>
        <Resource
          icon={HomeIcon}
          list={Home}
          name="Home"
          options={{ label: "Home" }}
        />
        <CustomRoutes noLayout>
          <Route element={<Navigate replace to="/Home" />} path="/" />
          <Route element={<Landing />} path="/Landing" />
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
- `Landing.tsx` is the optional no-layout companion route for the starter app.
- `children` inside `SchemaDrivenAdminApp` is the official custom-route
  extension point.
