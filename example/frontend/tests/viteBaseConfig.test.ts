// @vitest-environment node

import { describe, expect, it } from "vitest";

import viteConfig from "../vite.config";

describe("vite config", () => {
  it("uses the app base path and same-origin backend proxies", async () => {
    const config = await viteConfig({
      command: "serve",
      mode: "test",
      isSsrBuild: false,
      isPreview: false,
    });

    expect(config.base).toBe("/app/");
    expect(config.server?.proxy).toMatchObject({
      "/api": "http://127.0.0.1:5656",
      "/media": "http://127.0.0.1:5656",
      "/ui": "http://127.0.0.1:5656",
      "/jsonapi.json": "http://127.0.0.1:5656",
      "/swagger.json": "http://127.0.0.1:5656",
    });
  });
});
