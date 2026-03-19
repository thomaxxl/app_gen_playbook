# `frontend/vite.config.ts`

See also:

- [../../../specs/contracts/frontend/routing-and-paths.md](../../../specs/contracts/frontend/routing-and-paths.md)
- [../../../specs/contracts/deployment/README.md](../../../specs/contracts/deployment/README.md)

Use a Vite config that keeps same-origin development simple and handles the
`fs/promises` shim used by the current shared runtime.

```ts
import { fileURLToPath, URL } from "node:url";

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

function appDevBase() {
  return {
    name: "app-dev-base",
    configureServer(server) {
      server.middlewares.use((req, _res, next) => {
        if (req.url === "/app") {
          req.url = "/";
        } else if (req.url?.startsWith("/app/")) {
          req.url = req.url.replace(/^\/app/, "") || "/";
        }
        next();
      });
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendOrigin = env.VITE_BACKEND_ORIGIN || "http://127.0.0.1:5656";
  const fsPromisesShim = fileURLToPath(
    new URL("./src/shims/fs-promises.ts", import.meta.url),
  );

  return {
    base: "/app/",
    plugins: [appDevBase(), react()],
    resolve: {
      alias: {
        "fs/promises": fsPromisesShim,
        "node:fs/promises": fsPromisesShim,
      },
    },
    server: {
      strictPort: true,
      proxy: {
        "/api": backendOrigin,
        "/ui": backendOrigin,
        "/jsonapi.json": backendOrigin,
        "/swagger.json": backendOrigin,
      },
    },
  };
});
```

Notes:

- Use same-origin paths in the app and proxy them only in dev.
- `VITE_BACKEND_ORIGIN` is the launcher-controlled dev proxy target. Keep it
  overrideable so host and container runs can point at different backend ports
  without changing source code.
- Keep the frontend build deployable under `/app/`.
- The dev server MUST also respond on `/app/`; `base` alone is not
  sufficient for that in Vite dev mode, so the middleware rewrite above is
  part of the starter contract.
