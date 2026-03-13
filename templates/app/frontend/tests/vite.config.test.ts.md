# `frontend/tests/vite.config.test.ts`

See also:

- [../../../../specs/contracts/frontend/build-and-deploy.md](../../../../specs/contracts/frontend/build-and-deploy.md)
- [../vite.config.ts.md](../vite.config.ts.md)

Use a small config test so `/admin-app/` deployment assumptions stay
executable.

```ts
import { describe, expect, it } from "vitest";

import viteConfig from "../vite.config";

describe("vite config", () => {
  it("uses the admin-app base path and same-origin backend proxies", async () => {
    const config = await viteConfig({
      command: "serve",
      mode: "test",
      isSsrBuild: false,
      isPreview: false,
    });

    expect(config.base).toBe("/admin-app/");
    expect(config.server?.proxy).toMatchObject({
      "/api": "http://127.0.0.1:5656",
      "/ui": "http://127.0.0.1:5656",
      "/jsonapi.json": "http://127.0.0.1:5656",
      "/swagger.json": "http://127.0.0.1:5656",
    });
  });
});
```
