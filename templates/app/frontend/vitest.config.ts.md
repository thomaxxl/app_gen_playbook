# `frontend/vitest.config.ts`

See also:

- [../../../specs/contracts/frontend/validation.md](../../../specs/contracts/frontend/validation.md)

Use a minimal Vitest config with `jsdom` so the starter app has executable
frontend smoke tests.

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"],
  },
});
```
