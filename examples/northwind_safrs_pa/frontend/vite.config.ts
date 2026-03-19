import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const fsPromisesShim = fileURLToPath(
  new URL("./src/shims/fs-promises.ts", import.meta.url),
);
const projectRoot = fileURLToPath(new URL(".", import.meta.url));
const sharedRuntimeRoot = fileURLToPath(
  new URL("./src/shared-runtime", import.meta.url),
);

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "fs/promises": fsPromisesShim,
      "node:fs/promises": fsPromisesShim,
    },
    preserveSymlinks: true,
  },
  server: {
    fs: {
      allow: [projectRoot, sharedRuntimeRoot],
    },
  },
});
