import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig } from "@playwright/test";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const playwrightDbPath = path.join("/tmp", `cmdb-app-playwright-${process.pid}.sqlite`);

export default defineConfig({
  testDir: "./tests",
  testMatch: ["*.e2e.spec.ts"],
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
    command: "bash ./run.sh",
    cwd: path.resolve(__dirname, ".."),
    env: {
      BACKEND_HOST: "127.0.0.1",
      BACKEND_PORT: "5656",
      CMDB_APP_DB_PATH: playwrightDbPath,
      FRONTEND_HOST: "127.0.0.1",
      FRONTEND_PORT: "5173",
      FRONTEND_MODE: "preview",
    },
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    url: "http://127.0.0.1:5173/admin-app/",
  },
});
