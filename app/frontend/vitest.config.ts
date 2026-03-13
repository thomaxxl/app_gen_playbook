import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vitest/config";

const safrsJsonApiClientEntry = fileURLToPath(
  new URL("./node_modules/safrs-jsonapi-client/src/index.ts", import.meta.url),
);

export default defineConfig({
  resolve: {
    alias: {
      "safrs-jsonapi-client": safrsJsonApiClientEntry,
    },
  },
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"],
  },
});
