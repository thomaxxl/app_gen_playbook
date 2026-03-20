import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vitest/config";
export default defineConfig({
    resolve: {
        alias: {
            "safrs-jsonapi-client": fileURLToPath(new URL("./node_modules/safrs-jsonapi-client/src/index.ts", import.meta.url)),
        },
    },
    test: {
        environment: "jsdom",
        include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"],
    },
});
