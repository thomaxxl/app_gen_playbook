# `frontend/playwright.config.ts`

See also:

- [../../../specs/contracts/frontend/validation.md](../../../specs/contracts/frontend/validation.md)
- [../project/run.sh.md](../project/run.sh.md)

Use Playwright as the required browser-level delivery gate.

```ts
import { defineConfig } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  testDir: "./tests",
  testMatch: ["smoke.e2e.spec.ts"],
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: "http://127.0.0.1:5173",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: "./run.sh",
    cwd: path.resolve(__dirname, ".."),
    env: {
      BACKEND_HOST: "127.0.0.1",
      BACKEND_PORT: "5656",
      FRONTEND_HOST: "127.0.0.1",
      FRONTEND_PORT: "5173",
      FRONTEND_MODE: "preview",
    },
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    url: "http://127.0.0.1:5173/admin-app/",
  },
});
```

Notes:

- The starter smoke gate MUST run the combined app through `run.sh`.
- The canonical browser base path for the starter app is `/admin-app/`.
- Keep trace, screenshot, and video on failure so delivery regressions are
  diagnosable.
